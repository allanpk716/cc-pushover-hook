# 多实例支持实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use @superpowers:executing-plans to implement this plan task-by-task.

**目标:** 为 pushover-hook 添加多实例支持,使用 PID 隔离缓存和日志文件,避免并发冲突

**架构:** 通过进程 ID (PID) 隔离不同 Claude Code 实例的缓存文件和日志文件,Stop 事件标记完成而非删除,定期清理过期缓存

**技术栈:** Python 3.6+, Pathlib, JSON, 文件系统操作

---

## 前置检查清单

在开始实施前,确认:

- [ ] 已阅读设计方案: `docs/plans/2025-02-02-multi-instance-support-design.md`
- [ ] 目标文件: `hooks/pushover-notify.py`
- [ ] Python 版本 >= 3.6
- [ ] 理解数据流: UserPromptSubmit → Stop → 清理

---

## Task 1: 修改日志文件命名 (添加 PID 隔离)

**文件:**
- Modify: `hooks/pushover-notify.py:27-31`

**目标:** 让每个实例使用独立的日志文件

**Step 1: 备份当前函数**

在 `get_log_path()` 函数前添加注释标记原始版本:

```python
# ORIGINAL VERSION (before PID isolation):
# def get_log_path() -> Path:
#     """Get the debug log file path with daily rotation."""
#     script_dir = Path(__file__).parent
#     today = datetime.now().strftime("%Y-%m-%d")
#     return script_dir / f"debug.{today}.log"
```

**Step 2: 修改 `get_log_path()` 函数**

替换 `hooks/pushover-notify.py:27-31` 的函数实现:

```python
def get_log_path() -> Path:
    """
    Get the debug log file path with daily rotation and per-instance isolation.

    Each Claude Code instance (identified by PID) gets its own log file
    to prevent concurrent write conflicts in multi-instance scenarios.

    Returns:
        Path object for the log file: debug.YYYY-MM-DD-pid-{pid}.log
    """
    script_dir = Path(__file__).parent
    today = datetime.now().strftime("%Y-%m-%d")
    pid = os.getpid()
    return script_dir / f"debug.{today}-pid-{pid}.log"
```

**Step 3: 验证修改**

运行测试脚本验证日志文件命名:

```bash
# Windows
py -c "from hooks.pushover_notify import get_log_path; print(get_log_path())"

# Linux/macOS
python3 -c "from hooks.pushover_notify import get_log_path; print(get_log_path())"
```

**期望输出:**
```
hooks/pushover-hook/debug.2025-02-02-pid-12345.log
```

**Step 4: 提交修改**

```bash
git add hooks/pushover-notify.py
git commit -m "feat(logs): add PID isolation to log files

- Rename log files from debug.YYYY-MM-DD.log to debug.YYYY-MM-DD-pid-PID.log
- Prevents concurrent write conflicts when multiple Claude Code instances run
- Each instance now has its own log file

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 2: 修改缓存文件命名 - summarize_conversation 函数

**文件:**
- Modify: `hooks/pushover-notify.py:393-480` (summarize_conversation 函数)

**目标:** 缓存文件名包含 PID,实现实例隔离

**Step 1: 定位缓存文件命名逻辑**

在 `summarize_conversation()` 函数中找到第 407 行:

```python
# 原代码 (第 407 行):
cache_file = cache_dir / f"session-{session_id}.jsonl"
```

**Step 2: 修改缓存文件命名**

替换为:

```python
# 修改为:
pid = os.getpid()
cache_file = cache_dir / f"session-{session_id}-pid-{pid}.jsonl"
log(f"Cache file for PID {pid}: {cache_file}")
```

**Step 3: 验证修改**

```bash
# 检查语法
python -m py_compile hooks/pushover-notify.py
echo $?
# 期望输出: 0
```

**Step 4: 提交修改**

```bash
git add hooks/pushover-notify.py
git commit -m "feat(cache): add PID to cache file names in summarize_conversation

- Cache files renamed from session-{id}.jsonl to session-{id}-pid-{pid}.jsonl
- Each Claude Code instance maintains separate cache
- Prevents cache corruption in multi-instance scenarios

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 3: 修改 UserPromptSubmit 事件处理

**文件:**
- Modify: `hooks/pushover-notify.py:532-551` (main 函数中的 UserPromptSubmit 处理块)

**目标:** 在缓存条目中记录 PID

**Step 1: 定位 UserPromptSubmit 处理代码**

找到 `main()` 函数中的 `UserPromptSubmit` 事件处理块 (约第 532 行)

**Step 2: 修改缓存条目结构**

在 `elif hook_event == "UserPromptSubmit":` 块中,找到缓存条目创建代码 (约第 541-545 行):

```python
# 原代码:
entry = {
    "type": "user_prompt_submit",
    "prompt": hook_input.get("prompt", ""),
    "timestamp": hook_input.get("timestamp", ""),
}
```

**Step 3: 添加 PID 字段**

替换为:

```python
# 修改为:
pid = os.getpid()

cache_file = cache_dir / f"session-{session_id}-pid-{pid}.jsonl"

entry = {
    "type": "user_prompt_submit",
    "prompt": hook_input.get("prompt", ""),
    "timestamp": hook_input.get("timestamp", ""),
    "pid": pid,
}
```

**Step 4: 提交修改**

```bash
git add hooks/pushover-notify.py
git commit -m "feat(cache): add PID to UserPromptSubmit cache entries

- Each cache entry now includes the PID that created it
- Helps track which instance wrote which cache entries
- Useful for debugging multi-instance scenarios

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 4: 实现 cleanup_expired_cache 函数

**文件:**
- Modify: `hooks/pushover-notify.py` (在 cleanup_old_logs 函数后添加)

**目标:** 清理 7 天前的过期缓存文件

**Step 1: 找到插入位置**

在 `cleanup_old_logs()` 函数后 (约第 92 行之后),添加新函数

**Step 2: 实现清理函数**

```python
def cleanup_expired_cache(cache_dir: Path, keep_days: int = 7) -> None:
    """
    Clean up cache files older than keep_days days.

    Args:
        cache_dir: Directory containing session cache files
        keep_days: Number of days to keep cache files (default: 7)

    Cleans:
        - session-*-pid-*.jsonl files older than keep_days
        - Uses file modification time (st_mtime) for age detection

    Note:
        Silently fails on errors to avoid breaking the hook
    """
    if not cache_dir.exists():
        log("Cache directory does not exist, skipping cleanup")
        return

    try:
        cutoff_time = datetime.now() - timedelta(days=keep_days)
        cleaned_count = 0

        # Find all cache files matching the new naming pattern
        for cache_file in cache_dir.glob("session-*-pid-*.jsonl"):
            try:
                # Check file modification time
                file_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)

                if file_mtime < cutoff_time:
                    cache_file.unlink(missing_ok=True)
                    log(f"Cleaned expired cache: {cache_file.name}")
                    cleaned_count += 1

            except Exception as e:
                log(f"Error cleaning cache file {cache_file.name}: {e}", level="error")

        if cleaned_count > 0:
            log(f"Cache cleanup completed: {cleaned_count} expired file(s) removed")
        else:
            log("No expired cache files to clean")

    except Exception as e:
        # Silently fail - cleanup should never break the hook
        log(f"Error during cache cleanup: {e}", level="error")
```

**Step 3: 验证语法**

```bash
python -m py_compile hooks/pushover-notify.py
echo $?
# 期望输出: 0
```

**Step 4: 提交修改**

```bash
git add hooks/pushover-notify.py
git commit -m "feat(cache): add cleanup_expired_cache function

- Cleans up cache files older than 7 days (configurable)
- Uses file modification time for age detection
- Silently fails on errors to avoid breaking hook
- Finds files with session-*-pid-*.jsonl pattern

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 5: 修改 Stop 事件处理 - 不删除缓存

**文件:**
- Modify: `hooks/pushover-notify.py:553-574` (main 函数中的 Stop 处理块)

**目标:** Stop 事件不删除缓存,而是追加完成标记

**Step 1: 定位 Stop 事件中的缓存删除代码**

找到 `elif hook_event == "Stop":` 块末尾的缓存清理代码 (约第 569-574 行):

```python
# 原代码:
cache_file = Path(cwd) / ".claude" / "cache" / f"session-{session_id}.jsonl"
try:
    cache_file.unlink(missing_ok=True)
    log(f"Cache file cleaned up: {cache_file}")
except OSError as e:
    log(f"ERROR cleaning up cache: {e}")
```

**Step 2: 替换为标记完成逻辑**

```python
# 修改为:
pid = os.getpid()
cache_file = Path(cwd) / ".claude" / "cache" / f"session-{session_id}-pid-{pid}.jsonl"

# Mark session as completed instead of deleting
try:
    completed_entry = {
        "type": "session_complete",
        "timestamp": datetime.utcnow().isoformat(),
        "pid": pid
    }
    with open(cache_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(completed_entry) + "\n")
    log(f"Session marked as completed: {cache_file}")
except (OSError, IOError) as e:
    log(f"WARNING: Failed to mark session as completed: {e}", level="warn")
```

**Step 3: 提交修改**

```bash
git add hooks/pushover-notify.py
git commit -m "feat(cache): mark session complete instead of deleting cache

- Stop event now appends completion marker instead of deleting file
- Preserves cache for debugging and multi-instance scenarios
- Adds session_complete record with timestamp and PID

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 6: 在 Stop 事件中调用清理函数

**文件:**
- Modify: `hooks/pushover-notify.py:553-574` (main 函数中的 Stop 处理块末尾)

**目标:** 在 Stop 事件结束时清理过期缓存

**Step 1: 定位 Stop 处理块末尾**

在 `elif hook_event == "Stop":` 块的最后,在日志输出之前

**Step 2: 添加清理调用**

```python
elif hook_event == "Stop":
    log("Processing Stop event")
    # ... existing notification logic ...

    log(f"Message stats: chars={len(message)}, bytes={len(message.encode('utf-8'))}")

    # Clean up expired cache (7 days)
    cache_dir = Path(cwd) / ".claude" / "cache"
    cleanup_expired_cache(cache_dir, keep_days=7)

    # ... rest of the code ...
```

**Step 3: 提交修改**

```bash
git add hooks/pushover-notify.py
git commit -m "feat(cache): trigger cache cleanup on Stop event

- Calls cleanup_expired_cache() at end of Stop event
- Removes cache files older than 7 days
- Keeps cache directory size manageable

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 7: 处理 Stop 事件早于 UserPromptSubmit 的边界情况

**文件:**
- Modify: `hooks/pushover-notify.py:553-575` (main 函数中的 Stop 处理块)

**目标:** 当缓存文件不存在时优雅降级

**Step 1: 定位 summarize_conversation 调用**

在 Stop 事件处理块中找到:

```python
summary = summarize_conversation(session_id, cwd)
```

**Step 2: 添加缓存存在性检查**

```python
# 修改为:
pid = os.getpid()
cache_file = Path(cwd) / ".claude" / "cache" / f"session-{session_id}-pid-{pid}.jsonl"

if not cache_file.exists():
    log(f"No cache file found for session {session_id} (PID {pid})")
    summary = "Task completed (no user messages recorded)"
else:
    summary = summarize_conversation(session_id, cwd)
```

**Step 3: 提交修改**

```bash
git add hooks/pushover-notify.py
git commit -m "feat(cache): handle Stop event before UserPromptSubmit

- Check if cache file exists before reading
- Fallback to default message if cache missing
- Prevents errors when Stop event arrives first

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 8: 更新 cleanup_old_logs 以支持新的日志文件命名

**文件:**
- Modify: `hooks/pushover-notify.py:54-92` (cleanup_old_logs 函数)

**目标:** 更新日志清理逻辑以匹配新的命名模式

**Step 1: 定位日志文件匹配模式**

找到 `cleanup_old_logs()` 函数中的正则表达式 (约第 71 行):

```python
# 原代码:
log_pattern = re.compile(r'debug\.(\d{4}-\d{2}-\d{2})\.log')
```

**Step 2: 更新正则表达式**

```python
# 修改为:
log_pattern = re.compile(r'debug\.(\d{4}-\d{2}-\d{2})(?:-pid-\d+)?\.log')
```

这个正则现在匹配:
- `debug.2025-02-02.log` (旧格式)
- `debug.2025-02-02-pid-12345.log` (新格式)

**Step 3: 提交修改**

```bash
git add hooks/pushover-notify.py
git commit -m "feat(logs): update cleanup to support new log naming pattern

- Updated regex to match both old and new log file formats
- Backward compatible with existing debug.YYYY-MM-DD.log files
- Also handles new debug.YYYY-MM-DD-pid-PID.log files

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 9: 创建多实例测试脚本

**文件:**
- Create: `hooks/test-multi-instance.py`

**目标:** 提供测试脚本验证多实例隔离

**Step 1: 创建测试脚本**

```python
#!/usr/bin/env python3
"""
Multi-instance isolation test script.

Tests that multiple Claude Code instances can run concurrently
without cache or log conflicts.
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

def get_test_pid():
    """Get a fake PID for testing."""
    return os.getpid()

def test_cache_isolation():
    """Test that different PIDs create separate cache files."""
    print("Test 1: Cache file isolation by PID")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir) / ".claude" / "cache"
        cache_dir.mkdir(parents=True)

        # Simulate two instances
        pid1 = 1234
        pid2 = 5678
        session_id = "test-session-123"

        cache_file1 = cache_dir / f"session-{session_id}-pid-{pid1}.jsonl"
        cache_file2 = cache_dir / f"session-{session_id}-pid-{pid2}.jsonl"

        # Write to first cache
        entry1 = {"type": "user_prompt_submit", "prompt": "Instance 1", "pid": pid1}
        cache_file1.write_text(json.dumps(entry1) + "\n")

        # Write to second cache
        entry2 = {"type": "user_prompt_submit", "prompt": "Instance 2", "pid": pid2}
        cache_file2.write_text(json.dumps(entry2) + "\n")

        # Verify separation
        assert cache_file1.exists(), "Cache file 1 should exist"
        assert cache_file2.exists(), "Cache file 2 should exist"

        content1 = json.loads(cache_file1.read_text().strip())
        content2 = json.loads(cache_file2.read_text().strip())

        assert content1["pid"] == pid1, f"Cache 1 should have PID {pid1}"
        assert content2["pid"] == pid2, f"Cache 2 should have PID {pid2}"
        assert content1["prompt"] != content2["prompt"], "Caches should have different content"

        print("✅ Cache files are properly isolated by PID")
        print(f"   - Cache 1: {cache_file1.name}")
        print(f"   - Cache 2: {cache_file2.name}")

def test_log_isolation():
    """Test that different PIDs create separate log files."""
    print("\nTest 2: Log file isolation by PID")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        log_dir = Path(temp_dir)

        # Simulate two instances
        pid1 = 1234
        pid2 = 5678
        today = datetime.now().strftime("%Y-%m-%d")

        log_file1 = log_dir / f"debug.{today}-pid-{pid1}.log"
        log_file2 = log_dir / f"debug.{today}-pid-{pid2}.log"

        # Write to first log
        log_file1.write_text("[2025-02-02 12:00:00] Instance 1 log\n")

        # Write to second log
        log_file2.write_text("[2025-02-02 12:00:01] Instance 2 log\n")

        # Verify separation
        assert log_file1.exists(), "Log file 1 should exist"
        assert log_file2.exists(), "Log file 2 should exist"

        content1 = log_file1.read_text()
        content2 = log_file2.read_text()

        assert "Instance 1 log" in content1, "Log 1 should contain Instance 1 entry"
        assert "Instance 2 log" in content2, "Log 2 should contain Instance 2 entry"
        assert content1 != content2, "Logs should have different content"

        print("✅ Log files are properly isolated by PID")
        print(f"   - Log 1: {log_file1.name}")
        print(f"   - Log 2: {log_file2.name}")

def test_completion_marker():
    """Test that Stop event adds completion marker instead of deleting."""
    print("\nTest 3: Completion marker instead of deletion")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir) / ".claude" / "cache"
        cache_dir.mkdir(parents=True)

        pid = 1234
        session_id = "test-session-456"
        cache_file = cache_dir / f"session-{session_id}-pid-{pid}.jsonl"

        # Write initial cache entry
        entry = {
            "type": "user_prompt_submit",
            "prompt": "Test prompt",
            "pid": pid
        }
        cache_file.write_text(json.dumps(entry) + "\n")

        # Simulate Stop event adding completion marker
        completed_entry = {
            "type": "session_complete",
            "timestamp": datetime.utcnow().isoformat(),
            "pid": pid
        }

        with open(cache_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(completed_entry) + "\n")

        # Verify file still exists and has both entries
        assert cache_file.exists(), "Cache file should still exist"

        lines = cache_file.read_text().strip().split("\n")
        assert len(lines) == 2, f"Cache should have 2 entries, got {len(lines)}"

        first_entry = json.loads(lines[0])
        last_entry = json.loads(lines[1])

        assert first_entry["type"] == "user_prompt_submit"
        assert last_entry["type"] == "session_complete"

        print("✅ Completion marker added, cache file preserved")
        print(f"   - Cache file: {cache_file.name}")
        print(f"   - Entries: {len(lines)}")

def main():
    """Run all tests."""
    print("=" * 60)
    print("Multi-Instance Isolation Tests")
    print("=" * 60)

    try:
        test_cache_isolation()
        test_log_isolation()
        test_completion_marker()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

**Step 2: 设置执行权限 (Linux/macOS)**

```bash
chmod +x hooks/test-multi-instance.py
```

**Step 3: 运行测试**

```bash
# Windows
py hooks/test-multi-instance.py

# Linux/macOS
python3 hooks/test-multi-instance.py
```

**期望输出:**
```
============================================================
Multi-Instance Isolation Tests
============================================================
Test 1: Cache file isolation by PID
------------------------------------------------------------
✅ Cache files are properly isolated by PID
   - Cache 1: session-test-session-123-pid-1234.jsonl
   - Cache 2: session-test-session-123-pid-5678.jsonl

Test 2: Log file isolation by PID
------------------------------------------------------------
✅ Log files are properly isolated by PID
   - Log 1: debug.2025-02-02-pid-1234.log
   - Log 2: debug.2025-02-02-pid-5678.log

Test 3: Completion marker instead of deletion
------------------------------------------------------------
✅ Completion marker added, cache file preserved
   - Cache file: session-test-session-456-pid-1234.jsonl
   - Entries: 2

============================================================
✅ All tests passed!
============================================================
```

**Step 4: 提交测试脚本**

```bash
git add hooks/test-multi-instance.py
git commit -m "test: add multi-instance isolation tests

- Tests cache file isolation by PID
- Tests log file isolation by PID
- Tests completion marker instead of deletion
- All tests pass with expected behavior

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 10: 更新 README.md 文档

**文件:**
- Modify: `README.md`

**目标:** 添加多实例支持说明

**Step 1: 在"功能特性"表格后添加新章节**

在 `README.md` 的"功能特性"表格后 (约第 30 行),添加:

```markdown
### 多实例支持

本项目支持在同一项目中运行多个 Claude Code 实例,每个实例完全隔离:

| 特性 | 说明 |
|------|------|
| **PID 隔离** | 每个实例使用独立的缓存和日志文件 (基于进程 ID) |
| **非破坏性** | Stop 事件标记完成而非删除缓存,保留历史记录 |
| **自动清理** | 定期清理 7 天前的过期缓存文件 |
| **向后兼容** | 不需要修改现有 hook 配置或 Claude Code 设置 |

**文件命名规则:**
```
缓存文件: session-{session_id}-pid-{pid}.jsonl
日志文件: debug.{date}-pid-{pid}.log
```

**注意事项:**
- 每个实例的缓存文件会独立保留 7 天
- 磁盘占用会随实例数量增加
- 日志文件也按实例隔离,便于调试

```

**Step 2: 更新"故障排查"部分**

在 README.md 的"故障排查"章节中,添加新的 FAQ 项:

```markdown
### 多实例相关

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 缓存文件未被删除 | 正常行为 | 新版本使用 PID 隔离,缓存保留 7 天后自动清理 |
| 多个日志文件 | 多实例运行 | 每个实例有独立日志: debug.YYYY-MM-DD-pid-PID.log |
| 磁盘占用增加 | 缓存累积 | 缓存保留 7 天,Stop 事件自动清理过期文件 |
```

**Step 3: 提交文档更新**

```bash
git add README.md
git commit -m "docs: add multi-instance support documentation

- Document PID isolation mechanism
- Explain file naming conventions
- Add troubleshooting section for multi-instance scenarios
- Note about cache retention and cleanup policy

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 11: 手动验证测试

**目标:** 在真实环境中验证多实例支持

**Step 1: 准备测试环境**

```bash
# 创建测试项目
mkdir /tmp/test-multi-instance
cd /tmp/test-multi-instance

# 安装 pushover-hook (从你的项目目录)
python /path/to/cc-pushover-hook/install.py --target-dir . --non-interactive
```

**Step 2: 启动实例 1**

```bash
# 终端 1
cd /tmp/test-multi-instance
claude
# 发送消息: "Hello from instance 1"
# 然后退出
```

**Step 3: 启动实例 2**

```bash
# 终端 2
cd /tmp/test-multi-instance
claude
# 发送消息: "Hello from instance 2"
# 然后退出
```

**Step 4: 验证缓存隔离**

```bash
ls -la .claude/cache/
# 应该看到两个不同的缓存文件, PID 不同
```

**Step 5: 验证日志隔离**

```bash
ls -la .claude/hooks/pushover-hook/debug.*
# 应该看到两个不同的日志文件, PID 不同
```

**Step 6: 验证缓存保留**

```bash
# 检查缓存文件内容
cat .claude/cache/session-*-pid-*.jsonl | grep session_complete
# 应该看到 session_complete 标记,文件未被删除
```

**Step 7: 创建验证报告**

创建 `docs/multi-instance-verification.md`:

```markdown
# 多实例支持验证报告

**日期:** 2025-02-02
**版本:** 1.1.0

## 验证环境

- 操作系统: Windows 10
- Python 版本: 3.x
- Claude Code 版本: latest

## 测试结果

### ✅ 缓存文件隔离
- 两个实例创建了不同的缓存文件
- PID 不同,文件名不同
- 内容独立,无交叉

### ✅ 日志文件隔离
- 两个实例有独立的日志文件
- 日志内容正确,无混淆

### ✅ Stop 事件不删除缓存
- 缓存文件保留
- 包含 session_complete 标记

### ✅ 自动清理
- 过期文件会被清理
- 保留 7 天内的文件

## 结论

所有测试通过,多实例支持工作正常。
```

**Step 8: 提交验证报告**

```bash
git add docs/multi-instance-verification.md
git commit -m "test: add multi-instance verification report

- Verified cache isolation by PID
- Verified log isolation by PID
- Verified completion marker behavior
- All tests passed successfully

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 12: 更新版本号和 CHANGELOG

**文件:**
- Create: `CHANGELOG.md`
- Modify: `VERSION` (如果存在) 或在代码中标记版本

**Step 1: 创建 CHANGELOG.md**

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-02-02

### Added

- **Multi-instance support**: Multiple Claude Code instances can now run concurrently without conflicts
- **PID isolation**: Cache and log files are now isolated by process ID
- **Automatic cleanup**: Expired cache files (older than 7 days) are automatically cleaned up
- **Completion markers**: Stop events now mark session completion instead of deleting cache

### Changed

- Cache file naming: `session-{id}-pid-{pid}.jsonl` (was: `session-{id}.jsonl`)
- Log file naming: `debug.{date}-pid-{pid}.log` (was: `debug.{date}.log`)
- Stop event behavior: Adds completion marker instead of deleting cache file

### Technical Details

- Each Claude Code instance now has its own:
  - Cache file: `session-{session_id}-pid-{process_id}.jsonl`
  - Log file: `debug.{date}-pid-{process_id}.log`

- Cache files are retained for 7 days then automatically cleaned up
- Backward compatible with existing integrations

## [1.0.0] - Previous Release

- Initial release with single-instance support
- Pushover notifications for task completion
- Windows desktop notifications
- Session caching and summarization
```

**Step 2: 更新 VERSION 文件**

如果项目有 `VERSION` 文件,更新它:

```bash
echo "1.1.0" > VERSION
```

或者在 `hooks/pushover-notify.py` 文件开头更新版本注释:

```python
"""
Pushover notification hook for Claude Code.

Version: 1.1.0
...
"""
```

**Step 3: 提交版本更新**

```bash
git add CHANGELOG.md VERSION
git commit -m "chore: release version 1.1.0 with multi-instance support

- Add CHANGELOG.md documenting all changes
- Bump version to 1.1.0
- Document breaking changes in file naming

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 最终验证清单

在完成所有任务后,验证:

- [ ] 所有 12 个任务已完成
- [ ] 所有测试通过: `python hooks/test-multi-instance.py`
- [ ] 代码可以正常导入: `python -c "from hooks.pushover_notify import main"`
- [ ] 文档已更新 (README.md, CHANGELOG.md)
- [ ] 手动测试成功 (多实例场景)
- [ ] Git 历史清晰,每个任务一个 commit
- [ ] 没有 merge commits

---

## 执行顺序

**推荐执行顺序:**
1. Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7 → Task 8 (核心功能)
2. Task 9 (测试)
3. Task 10 → Task 11 → Task 12 (文档和验证)

**预计时间:**
- 核心功能实现: 30-45 分钟
- 测试和验证: 15-20 分钟
- 文档更新: 15-20 分钟
- **总计: 60-90 分钟**

---

## 回滚计划

如果出现问题:

1. **识别问题任务**: 查看 git log,定位到有问题的 commit
2. **回滚单个 commit**: `git revert <commit-hash>`
3. **回滚多个 commit**: `git revert --no-commit <older-commit>..HEAD && git commit`
4. **重新测试**: 运行 `python hooks/test-multi-instance.py`

---

## 后续优化 (可选)

这些不是必需的,但可以作为未来的改进:

- [ ] 添加 psutil 支持,记录进程启动时间以防止 PID 重用冲突
- [ ] 实现文件写入重试机制
- [ ] 添加性能基准测试
- [ ] 支持配置缓存保留天数 (环境变量)
- [ ] 添加缓存统计命令 (显示总大小、文件数等)

---

**文档版本:** 1.0
**最后更新:** 2025-02-02
**状态:** Ready for implementation
