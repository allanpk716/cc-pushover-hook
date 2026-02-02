# 多实例支持设计方案

**日期**: 2025-02-02
**版本**: 1.0
**状态**: 设计完成，待实施

---

## 问题背景

当同一个项目启动多个 Claude Code 实例时，现有的 pushover-hook 会出现冲突问题：

### 核心问题

1. **缓存文件冲突**
   - 所有实例共享同一个缓存文件：`session-{session_id}.jsonl`
   - 多个实例同时写入可能导致数据覆盖
   - Stop 事件删除缓存文件，导致其他实例数据丢失

2. **日志文件冲突**
   - 所有实例共享同一个日志文件：`debug.{date}.log`
   - 并发写入导致日志内容错乱

3. **无进程锁机制**
   - 完全没有文件锁或进程同步机制
   - 多个实例可能同时执行 Stop 事件的处理逻辑

---

## 解决方案：PID 隔离 + 惰性标记 + 定期清理

### 核心设计原则

1. **实例隔离**: 每个实例通过进程 ID (PID) 拥有独立的缓存和日志文件
2. **非破坏性操作**: Stop 事件不删除缓存，而是追加完成标记
3. **惰性清理**: 只在 Stop 事件时触发过期缓存清理
4. **向后兼容**: 保持现有 hook 输入格式不变

---

## 架构设计

### 文件命名规则

```
缓存文件: session-{session_id}-pid-{pid}.jsonl
日志文件: debug.{date}-pid-{pid}.log
完成标记: 在缓存文件末尾追加 session_complete 记录
```

### 数据流

#### UserPromptSubmit 事件
```
1. 获取当前进程 PID
2. 写入独立的缓存文件 (追加模式)
3. 记录到独立的日志文件
```

#### Stop 事件
```
1. 获取当前进程 PID
2. 读取独立的缓存文件
3. 生成并发送通知
4. 在缓存文件中追加完成标记 (不删除)
5. 清理 7 天前的所有过期文件
```

#### Notification 事件
```
1. 获取当前进程 PID
2. 直接发送通知 (不涉及缓存)
3. 记录到独立的日志文件
```

---

## 核心组件修改

### 1. 缓存管理重构

#### 修改点 A: 缓存文件命名

**文件**: `hooks/pushover-notify.py`

**位置**: `summarize_conversation()` 函数 (第 407 行)

```python
# 原来:
cache_file = cache_dir / f"session-{session_id}.jsonl"

# 改为:
import os
pid = os.getpid()
cache_file = cache_dir / f"session-{session_id}-pid-{pid}.jsonl"
```

#### 修改点 B: UserPromptSubmit 事件处理

**文件**: `hooks/pushover-notify.py`

**位置**: `main()` 函数，`UserPromptSubmit` 事件处理块 (第 538 行)

```python
# 原来:
cache_file = cache_dir / f"session-{session_id}.jsonl"

# 改为:
pid = os.getpid()
cache_file = cache_dir / f"session-{session_id}-pid-{pid}.jsonl"

# 记录 PID 到缓存条目
entry = {
    "type": "user_prompt_submit",
    "prompt": hook_input.get("prompt", ""),
    "timestamp": hook_input.get("timestamp", ""),
    "pid": pid
}
```

#### 修改点 C: Stop 事件不删除文件

**文件**: `hooks/pushover-notify.py`

**位置**: `main()` 函数，`Stop` 事件处理块 (第 569-574 行)

```python
# 原来:
cache_file.unlink(missing_ok=True)
log(f"Cache file cleaned up: {cache_file}")

# 改为:
# 追加完成标记
from datetime import datetime
completed_entry = {
    "type": "session_complete",
    "timestamp": datetime.utcnow().isoformat(),
    "pid": pid
}
try:
    with open(cache_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(completed_entry) + "\n")
    log(f"Session marked as completed: {cache_file}")
except (OSError, IOError) as e:
    log(f"WARNING: Failed to mark session as completed: {e}")
```

### 2. 日志系统重构

**文件**: `hooks/pushover-notify.py`

**位置**: `get_log_path()` 函数 (第 27-31 行)

```python
# 原来:
def get_log_path() -> Path:
    """Get the debug log file path with daily rotation."""
    script_dir = Path(__file__).parent
    today = datetime.now().strftime("%Y-%m-%d")
    return script_dir / f"debug.{today}.log"

# 改为:
def get_log_path() -> Path:
    """Get the debug log file path with daily rotation and per-instance isolation."""
    script_dir = Path(__file__).parent
    today = datetime.now().strftime("%Y-%m-%d")
    pid = os.getpid()
    return script_dir / f"debug.{today}-pid-{pid}.log"
```

### 3. 新增清理函数

**文件**: `hooks/pushover-notify.py`

**位置**: 在 `cleanup_old_logs()` 函数之后添加

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
        return

    try:
        cutoff_time = datetime.now() - timedelta(days=keep_days)
        cache_pattern = re.compile(r'session-.*-pid-\d+\.jsonl')

        cleaned_count = 0
        for cache_file in cache_dir.glob("session-*-pid-*.jsonl"):
            try:
                # Check file modification time
                file_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)

                if file_mtime < cutoff_time:
                    cache_file.unlink(missing_ok=True)
                    log(f"Cleaned expired cache: {cache_file.name}")
                    cleaned_count += 1

            except Exception as e:
                log(f"Error cleaning cache file {cache_file.name}: {e}")

        if cleaned_count > 0:
            log(f"Cache cleanup completed: {cleaned_count} expired file(s) removed")

    except Exception as e:
        # Silently fail - cleanup should never break the hook
        log(f"Error during cache cleanup: {e}")
```

**调用位置**: `main()` 函数，`Stop` 事件处理块末尾

```python
elif hook_event == "Stop":
    # ... existing notification logic ...

    # Clean up expired cache (7 days)
    cache_dir = Path(cwd) / ".claude" / "cache"
    cleanup_expired_cache(cache_dir, keep_days=7)
```

---

## 错误处理与边界情况

### 1. Stop 事件早于 UserPromptSubmit

**场景**: 实例只收到 Stop 事件，没有收到 UserPromptSubmit

**处理**:
```python
if not cache_file.exists():
    log(f"No cache file found for session {session_id} (PID {pid})")
    summary = "Task completed (no user messages recorded)"
else:
    summary = summarize_conversation(session_id, cwd)
```

### 2. 并发写入同一缓存文件

**场景**: 同一实例的多个 UserPromptSubmit 事件并发写入

**处理**: Python 的文件追加写入 (O_APPEND) 在大多数操作系统上是原子性的
- **可选增强**: 实现重试机制 (见下文)

#### 可选增强: 文件写入重试

```python
def append_to_cache(cache_file: Path, entry: dict, max_retries: int = 3) -> bool:
    """Append entry to cache file with retry on failure."""
    import time

    for attempt in range(max_retries):
        try:
            with open(cache_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
            return True
        except (OSError, IOError) as e:
            if attempt == max_retries - 1:
                log(f"ERROR: Failed to write cache after {max_retries} attempts: {e}")
                return False
            time.sleep(0.01 * (attempt + 1))  # Exponential backoff
    return False
```

### 3. PID 重用问题 (极低概率)

**场景**: 进程 A 结束后，OS 重用 PID 给进程 B

**风险**: 进程 B 可能误读写进程 A 的缓存

#### 可选增强: 进程启动时间记录

**依赖**: `psutil` 库

```python
# 在缓存条目中记录进程启动时间
def get_process_start_time() -> float:
    """Get process start time for PID collision detection."""
    try:
        import psutil
        return psutil.Process(os.getpid()).create_time()
    except Exception:
        import time
        return time.time()

# UserPromptSubmit 缓存条目
entry = {
    "type": "user_prompt_submit",
    "prompt": hook_input.get("prompt", ""),
    "timestamp": hook_input.get("timestamp", ""),
    "pid": pid,
    "process_start": get_process_start_time()  # 新增
}
```

**依赖处理**:
```python
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    log("psutil not available, PID collision detection disabled")
```

---

## 实施计划

### 阶段 1: 核心功能实现 (必须)

- [ ] 修改缓存文件命名逻辑 (添加 PID)
- [ ] 修改日志文件命名逻辑 (添加 PID)
- [ ] 修改 Stop 事件处理 (不删除，追加标记)
- [ ] 实现 `cleanup_expired_cache()` 函数
- [ ] 在 Stop 事件中调用清理函数

### 阶段 2: 增强功能 (可选)

- [ ] 实现进程启动时间获取 (需要 psutil)
- [ ] 实现文件写入重试机制
- [ ] 实现文件占用检测

### 阶段 3: 测试与验证

- [ ] 单元测试: 模拟多实例场景
- [ ] 手动测试: 真实多实例并发
- [ ] 压力测试: 并发 UserPromptSubmit + Stop

---

## 测试计划

### 测试用例 1: 基本多实例隔离

**步骤**:
```bash
# 终端 1: 启动实例 A
cd /path/to/project
claude  # 实例 A, PID=1234

# 终端 2: 启动实例 B
cd /path/to/project
claude  # 实例 B, PID=5678
```

**验证**:
```bash
ls .claude/cache/
# 期望输出:
# session-xxx-pid-1234.jsonl
# session-yyy-pid-5678.jsonl
```

### 测试用例 2: Stop 事件不删除缓存

**步骤**:
1. 在实例中完成任务
2. 检查缓存文件是否存在

**验证**:
```bash
cat .claude/cache/session-xxx-pid-1234.jsonl
# 期望看到最后一行:
# {"type": "session_complete", "timestamp": "...", "pid": 1234}
```

### 测试用例 3: 过期清理

**步骤**:
```bash
# 创建一个 7 天前的缓存文件 (Linux/macOS)
touch -t 202501260000 .claude/cache/session-old-pid-9999.jsonl

# 触发 Stop 事件
```

**验证**:
```bash
ls .claude/cache/
# 旧文件应被删除，新文件保留
```

### 测试用例 4: 并发写入

**步骤**:
快速连续发送多个 UserPromptSubmit 事件

**验证**:
所有消息都被正确记录到缓存文件

### 测试用例 5: 日志隔离

**步骤**:
启动多个 Claude Code 实例

**验证**:
```bash
ls .claude/hooks/pushover-hook/debug.*
# 期望输出:
# debug.2025-02-02-pid-1234.log
# debug.2025-02-02-pid-5678.log
```

---

## 影响评估

### 优势

✅ **完全隔离**: 多实例无冲突，独立运行
✅ **向后兼容**: 不需要修改 Claude Code 或 hook 输入格式
✅ **实施简单**: 修改点少，风险可控
✅ **可调试性**: 保留历史数据便于问题排查

### 注意事项

⚠️ **文件数量增加**: 每个实例一个缓存文件
⚠️ **磁盘占用增加**: 缓存保留 7 天
⚠️ **PID 重用**: 理论上存在极低概率 (通过进程启动时间缓解)

### 性能影响

- **Stop 事件**: 增加清理时间 (通常 <100ms)
- **文件写入**: 增加重试机制 (几乎无影响)
- **日志性能**: 独立日志文件，无锁竞争

---

## 文档更新

### 需要更新的文档

1. **README.md**
   - 添加"多实例支持"章节
   - 说明隔离机制
   - 更新故障排查部分

2. **INTEGRATION.md**
   - 说明 PID 隔离机制
   - 更新集成示例

3. **FAQ** (新增)
   - "多个 Claude Code 实例会冲突吗?"
   - "缓存文件为什么没有被删除?"
   - "如何调整缓存保留时间?"

---

## 版本信息

- **设计方案版本**: 1.0
- **目标实现版本**: 1.1.0
- **预计实施时间**: 待定
- **实施负责人**: 待定

---

## 变更历史

| 日期 | 版本 | 变更说明 | 作者 |
|------|------|----------|------|
| 2025-02-02 | 1.0 | 初始设计方案 | Claude Code |
