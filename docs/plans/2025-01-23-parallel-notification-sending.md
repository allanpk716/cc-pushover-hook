# 并行通知发送实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** Windows 本地通知立即显示，不等待 Pushover 网络请求。

**架构:** 使用 Python `concurrent.futures.ThreadPoolExecutor` 并行发送两个通知，每个在独立线程中执行，互不阻塞。

**技术栈:** Python 3.2+ 标准库 `concurrent.futures`，无需额外依赖。

---

### Task 1: 导入 ThreadPoolExecutor

**文件:**
- 修改: `.claude/hooks/pushover-hook/pushover-notify.py:10-16`

**Step 1: 添加导入语句**

在现有导入区域（第 16 行之后）添加：

```python
from concurrent.futures import ThreadPoolExecutor
```

完整导入区域应变为：

```python
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
```

**Step 2: 验证语法**

运行: `python -m py_compile .claude/hooks/pushover-hook/pushover-notify.py`
预期: 无错误输出

**Step 3: 提交**

```bash
git add .claude/hooks/pushover-hook/pushover-notify.py
git commit -m "feat: import ThreadPoolExecutor for parallel notifications"
```

---

### Task 2: 重写 send_notifications 函数为并行实现

**文件:**
- 修改: `.claude/hooks/pushover-hook/pushover-notify.py:332-365`

**Step 1: 备份原函数**

在第 332 行 `send_notifications` 函数上方添加注释：

```python
# OLD SERIAL IMPLEMENTATION (removed - replaced with parallel)
# def send_notifications_OLD(title: str, message: str, priority: int = 0, cwd: str = "") -> dict:
#     results = {"pushover": False, "windows": False}
#     pushover_disabled = cwd and is_notification_disabled(cwd)
#     windows_disabled = cwd and is_windows_notification_disabled(cwd)
#     if pushover_disabled and windows_disabled:
#         log("All notifications disabled")
#         return results
#     if not pushover_disabled:
#         results["pushover"] = _send_pushover_internal(title, message, priority, cwd)
#     if not windows_disabled and sys.platform == "win32":
#         results["windows"] = send_windows_notification(title, message)
#     elif not windows_disabled and sys.platform != "win32":
#         log("Windows native notification not supported on this platform")
#     return results
```

**Step 2: 替换函数实现**

将 `send_notifications` 函数（第 332-365 行）完全替换为：

```python
def send_notifications(title: str, message: str, priority: int = 0, cwd: str = "") -> dict:
    """
    Send notifications via enabled channels in parallel.

    Windows local notifications display immediately without waiting for Pushover API.

    Args:
        title: Notification title
        message: Notification message body
        priority: Message priority (for Pushover, -2 to 2, default 0)
        cwd: Current working directory to check for disable files

    Returns:
        Dict with status of each channel: {"pushover": bool, "windows": bool}
    """
    results = {"pushover": False, "windows": False}

    # Check if both are disabled
    pushover_disabled = cwd and is_notification_disabled(cwd)
    windows_disabled = cwd and is_windows_notification_disabled(cwd)

    if pushover_disabled and windows_disabled:
        log("All notifications disabled (.no-pushover and .no-windows both exist)")
        return results

    futures = {}

    # Use ThreadPoolExecutor for parallel execution
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Submit Pushover notification if enabled
        if not pushover_disabled:
            log("Starting Pushover notification thread")
            futures["pushover"] = executor.submit(
                _send_pushover_internal, title, message, priority, cwd
            )

        # Submit Windows notification if enabled and on Windows
        if not windows_disabled and sys.platform == "win32":
            log("Starting Windows notification thread")
            futures["windows"] = executor.submit(
                send_windows_notification, title, message
            )
        elif not windows_disabled and sys.platform != "win32":
            log("Windows native notification not supported on this platform")

        # Wait for results with timeout
        for name, future in futures.items():
            try:
                results[name] = future.result(timeout=10)
                log(f"{name.capitalize()} notification thread completed: {results[name]}")
            except Exception as e:
                log(f"ERROR: {name} notification thread failed: {e}")
                results[name] = False

    return results
```

**Step 3: 验证语法**

运行: `python -m py_compile .claude/hooks/pushover-hook/pushover-notify.py`
预期: 无错误输出

**Step 4: 提交**

```bash
git add .claude/hooks/pushover-hook/pushover-notify.py
git commit -m "feat: send notifications in parallel using ThreadPoolExecutor"
```

---

### Task 3: 手动测试并行发送

**文件:**
- 创建: `.claude/hooks/pushover-hook/test-parallel-notifications.py`

**Step 1: 创建测试脚本**

```python
#!/usr/bin/env python3
"""Test parallel notification sending with slow Pushover simulation."""

import sys
import time
from pathlib import Path

# Add script directory to path for imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from pushover_notify import send_notifications, log

def test_parallel_speed():
    """Test that Windows notification completes quickly even with slow Pushover."""
    print("=" * 60)
    print("Testing parallel notification sending...")
    print("=" * 60)

    # Simulate slow network by using a test that completes
    # In real usage, Pushover might take 2-5 seconds on slow networks
    start = time.time()

    title = "[Test] Parallel Notifications"
    message = "Session: test-123\\nSummary: Testing parallel execution"

    log("Starting test: parallel notifications")
    results = send_notifications(title, message, priority=0, cwd=".")

    elapsed = time.time() - start

    print(f"\nResults:")
    print(f"  Pushover: {results['pushover']}")
    print(f"  Windows:  {results['windows']}")
    print(f"  Total time: {elapsed:.2f}s")

    # Windows notification should complete quickly (< 2s)
    # even if Pushover is slow (network delay)
    if results['windows']:
        print("\n✓ Windows notification sent successfully")

        if elapsed < 3.0:
            print(f"✓ Completed in reasonable time ({elapsed:.2f}s < 3s)")
        else:
            print(f"⚠ Took longer than expected ({elapsed:.2f}s)")
    else:
        print("\n✗ Windows notification failed")

    print("=" * 60)
    return results

if __name__ == "__main__":
    test_parallel_speed()
```

**Step 2: 运行测试**

运行: `python .claude/hooks/pushover-hook/test-parallel-notifications.py`
预期: 看到 Windows 通知快速弹出（< 1 秒），即使 Pushover 需要更长时间

**Step 3: 检查日志**

运行: `type .claude\hooks\pushover-hook\debug.log`
预期: 看到 "Starting Pushover notification thread" 和 "Starting Windows notification thread" 日志

**Step 4: 提交测试脚本**

```bash
git add .claude/hooks/pushover-hook/test-parallel-notifications.py
git commit -m "test: add parallel notification test script"
```

---

### Task 4: 更新 CHANGELOG

**文件:**
- 修改: `CHANGELOG.md`

**Step 1: 在文件顶部添加新条目**

在 `[Unreleased]` 部分添加：

```markdown
## [Unreleased]

### Added
- 并行发送通知：Windows 本地通知立即显示，不等待 Pushover API 响应

### Changed
- `send_notifications` 函数使用 `ThreadPoolExecutor` 并行执行
```

**Step 2: 提交**

```bash
git add CHANGELOG.md
git commit -m "docs: update CHANGELOG for parallel notifications"
```

---

### Task 5: 清理旧代码注释

**文件:**
- 修改: `.claude/hooks/pushover-hook/pushover-notify.py:332`

**Step 1: 移除备份注释**

删除 Task 2 中添加的 `# OLD SERIAL IMPLEMENTATION` 注释块（约 15 行）

**Step 2: 提交**

```bash
git add .claude/hooks/pushover-hook/pushover-notify.py
git commit -m "style: remove old implementation comment"
```

---

## 验证清单

完成所有任务后，验证：

- [ ] `python -m py_compile` 无错误
- [ ] 运行 `test-parallel-notifications.py`，Windows 通知在 1 秒内显示
- [ ] 检查 `debug.log` 确认并行日志
- [ ] 测试 `.no-pushover` 文件仍生效
- [ ] 测试 `.no-windows` 文件仍生效
- [ ] CHANGELOG.md 已更新

## 相关文档

- 设计文档: `docs/plans/2025-01-23-parallel-notification-sending-design.md`
- Windows 通知设计: `docs/plans/2025-01-21-windows-notification-design.md`
