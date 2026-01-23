# 并行通知发送设计

## 问题

当前 `pushover-notify.py` 中通知发送是串行的：先发送 Pushover 请求，等待完成后才发送 Windows 通知。当 Pushover API 响应慢时，Windows 通知会被延迟显示。

## 目标

Windows 本地通知应立即显示，不等待 Pushover 网络请求完成。

## 方案

使用 Python `concurrent.futures.ThreadPoolExecutor` 并行发送两个通知。

### 架构改动

**原逻辑（串行）：**
```
发送 Pushover → 等待完成 → 发送 Windows 通知
```

**新逻辑（并行）：**
```
同时启动两个线程：
├─ 线程1: 发送 Pushover
└─ 线程2: 发送 Windows 通知（本地，很快）
等待两者完成（或超时）
```

### 代码实现

```python
from concurrent.futures import ThreadPoolExecutor

def send_notifications(title: str, message: str, priority: int = 0, cwd: str = "") -> dict:
    results = {"pushover": False, "windows": False}

    pushover_disabled = cwd and is_notification_disabled(cwd)
    windows_disabled = cwd and is_windows_notification_disabled(cwd)

    if pushover_disabled and windows_disabled:
        log("All notifications disabled")
        return results

    futures = {}

    with ThreadPoolExecutor(max_workers=2) as executor:
        if not pushover_disabled:
            futures["pushover"] = executor.submit(
                _send_pushover_internal, title, message, priority, cwd
            )

        if not windows_disabled and sys.platform == "win32":
            futures["windows"] = executor.submit(
                send_windows_notification, title, message
            )

        for name, future in futures.items():
            try:
                results[name] = future.result(timeout=10)
            except Exception as e:
                log(f"ERROR: {name} notification failed: {e}")
                results[name] = False

    return results
```

## 错误处理

每个通知通道独立处理错误，互不影响。

| 场景 | 行为 |
|------|------|
| Windows 成功，Pushover 超时 | Windows 已显示，Pushover 标记失败 |
| Windows 失败，Pushover 成功 | Pushover 已发送，Windows 标记失败 |
| 两者都失败 | 记录日志，返回失败状态 |

## 测试策略

### 单元测试
- 模拟 Pushover 延迟 5 秒，验证 Windows 通知在 100ms 内完成
- 模拟超时和异常场景

### 手动验证
- 限制网络速度，观察 Windows 通知是否立即显示
- 检查 `debug.log` 确认并行执行

## 兼容性

- `concurrent.futures` 是 Python 3.2+ 标准库，无需额外依赖
- 函数签名和返回值格式不变
- 现有配置文件（`.no-pushover`, `.no-windows`）无变化

## 实施清单

- [ ] 导入 `ThreadPoolExecutor`
- [ ] 重写 `send_notifications` 函数
- [ ] 添加线程启停日志
- [ ] 本地测试验证
- [ ] 更新 CHANGELOG.md
