# Claude Code Pushover 通知 Hook

为 Claude Code 添加 Pushover 通知功能，在任务完成或需要人工干预时发送通知到你的设备。同时可作为独立通知模块集成到其他应用。

---

## 目录

- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [用户使用指南](#用户使用指南)
- [开发者集成指南](#开发者集成指南)
- [配置选项](#配置选项)
- [故障排查](#故障排查)

---

## 功能特性

| 特性 | 说明 |
|------|------|
| **任务完成通知** | Claude Code 完成任务响应时自动发送通知 |
| **需要关注通知** | 需要权限请求、Plan 模式询问或其他需要交互时发送高优先级通知 |
| **智能过滤** | 自动过滤 CLI 空闲提醒（idle_prompt），只在真正需要交互时通知 |
| **项目级禁用** | 通过创建 `.no-pushover` 文件即可临时禁用单个项目的通知 |
| **AI 任务摘要** | 使用 Claude CLI 自动生成任务摘要 |
| **跨平台支持** | 支持 Windows、Linux 和 macOS |
| **并行通知** | 同时发送 Pushover 和 Windows 本地通知 |
| **降级策略** | CLI 调用失败时自动降级 |
| **日志轮转** | 自动清理 3 天前的调试日志 |

---

## 快速开始

### 前置要求

- Python 3.6+
- curl（Windows 10+、Linux、macOS 通常已内置）

### 一键安装

```bash
# 1. 克隆或下载此项目
git clone https://github.com/your-repo/cc-pushover-hook.git
cd cc-pushover-hook

# 2. 运行安装脚本
python install.py

# 3. 设置环境变量（见下方）

# 4. 发送测试通知
python .claude/hooks/pushover-hook/test-pushover.py
```

### 环境变量设置

```bash
# Linux/macOS - 添加到 ~/.bashrc 或 ~/.zshrc
export PUSHOVER_TOKEN="your_api_token_here"
export PUSHOVER_USER="your_user_key_here"

# Windows PowerShell
$env:PUSHOVER_TOKEN="your_api_token_here"
$env:PUSHOVER_USER="your_user_key_here"

# Windows 系统环境变量（永久）
# 1. 右键"此电脑" -> "属性" -> "高级系统设置"
# 2. 点击"环境变量"
# 3. 添加用户变量：
#    PUSHOVER_TOKEN = your_api_token_here
#    PUSHOVER_USER  = your_user_key_here
```

> **获取凭证：** 访问 [Pushover.net](https://pushover.net/) 注册账号并创建应用获取 API Token 和 User Key

---

## 用户使用指南

### 安装到项目

#### 方法一：自动安装（推荐）

```bash
python install.py
```

安装脚本会：
- 检测你的操作系统
- 询问目标项目路径
- 复制所有必要文件
- 生成适合你系统的 settings.json
- 引导完成环境变量设置
- 运行诊断验证安装

#### 方法二：手动安装

```bash
# 复制整个 .claude 目录到你的项目根目录
cp -r .claude /path/to/your-project/

# Linux/macOS 设置执行权限
chmod +x .claude/hooks/pushover-hook/*.py
```

### 验证安装

```bash
# 运行诊断脚本
python .claude/hooks/pushover-hook/diagnose.py

# 发送测试通知
python .claude/hooks/pushover-hook/test-pushover.py

# 手动测试 Hook
echo '{"hook_event_name":"Stop","session_id":"test123","cwd":"/path/to/project"}' | \
  python .claude/hooks/pushover-hook/pushover-notify.py
```

### 通知场景

| 场景 | 优先级 | 示例 |
|------|--------|------|
| **任务完成** | 0 (正常) | `[ProjectName] Task Complete` |
| **需要关注** | 1 (高) | `[ProjectName] Attention Needed` |
| **权限请求** | 1 (高) | 需要批准运行命令或修改文件 |

### 项目级禁用通知

```bash
# 禁用 Pushover 通知
touch .no-pushover          # Linux/macOS
type nul > .no-pushover     # Windows

# 禁用 Windows 本地通知
touch .no-windows           # Linux/macOS
type nul > .no-windows      # Windows

# 恢复通知 - 删除对应文件即可
rm .no-pushover .no-windows
```

---

## 开发者集成指南

### 概述

`pushover-notify.py` 是一个独立的 Python 脚本，可以通过 **标准输入 (stdin)** 接收 JSON 格式的触发事件，实现应用集成。

### 接口规范

#### 输入格式 (stdin JSON)

```json
{
  "hook_event_name": "Stop|UserPromptSubmit|Notification",
  "session_id": "unique_session_identifier",
  "cwd": "/path/to/working/directory",
  "prompt": "user_message_content",        // UserPromptSubmit 时使用
  "notification_type": "type_name",        // Notification 时使用
  "message": "notification_message",       // Notification 时使用
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### 事件类型

| 事件 | 触发时机 | 行为 |
|------|----------|------|
| `UserPromptSubmit` | 用户提交消息时 | 缓存用户输入到 `.claude/cache/` |
| `Stop` | 会话结束时 | 发送任务完成通知，清理缓存 |
| `Notification` | 需要关注时 | 发送高优先级通知（排除 idle_prompt） |

### 集成示例

#### Python 集成

```python
import subprocess
import json
import os

def send_notification(event_type: str, session_id: str, project_path: str, **kwargs):
    """调用 pushover-notify.py 发送通知"""
    hook_script = os.path.join(
        os.path.dirname(__file__),
        ".claude/hooks/pushover-hook/pushover-notify.py"
    )

    payload = {
        "hook_event_name": event_type,
        "session_id": session_id,
        "cwd": project_path,
        **kwargs
    }

    result = subprocess.run(
        ["python", hook_script],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

    return result.returncode == 0

# 使用示例
send_notification(
    event_type="Stop",
    session_id="sess-123",
    project_path="/path/to/project"
)
```

#### Node.js 集成

```javascript
const { spawn } = require('child_process');
const path = require('path');

function sendNotification(eventType, sessionId, projectPath, extra = {}) {
  const hookScript = path.join(__dirname, '.claude/hooks/pushover-hook/pushover-notify.py');
  const payload = {
    hook_event_name: eventType,
    session_id: sessionId,
    cwd: projectPath,
    ...extra
  };

  return new Promise((resolve) => {
    const child = spawn('python', [hookScript], {
      stdio: ['pipe', 'inherit', 'inherit']
    });

    child.stdin.write(JSON.stringify(payload));
    child.stdin.end();

    child.on('close', (code) => resolve(code === 0));
  });
}

// 使用示例
await sendNotification('Stop', 'sess-123', '/path/to/project');
```

#### Bash 集成

```bash
#!/bin/bash
# send-notification.sh

HOOK_SCRIPT=".claude/hooks/pushover-hook/pushover-notify.py"
PROJECT_PATH="$(pwd)"
SESSION_ID="sess-$(date +%s)"

# 发送 Stop 通知
echo "{
  \"hook_event_name\": \"Stop\",
  \"session_id\": \"$SESSION_ID\",
  \"cwd\": \"$PROJECT_PATH\"
}" | python "$HOOK_SCRIPT"
```

#### Go 集成

```go
package main

import (
    "bytes"
    "encoding/json"
    "os/exec"
)

type HookPayload struct {
    HookEventName string `json:"hook_event_name"`
    SessionID     string `json:"session_id"`
    CWD           string `json:"cwd"`
}

func SendNotification(eventType, sessionID, cwd string) error {
    payload := HookPayload{
        HookEventName: eventType,
        SessionID:     sessionID,
        CWD:           cwd,
    }

    data, _ := json.Marshal(payload)
    cmd := exec.Command("python", ".claude/hooks/pushover-hook/pushover-notify.py")
    cmd.Stdin = bytes.NewReader(data)

    return cmd.Run()
}
```

### Claude Code Hook 配置

在 `.claude/settings.json` 中配置：

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "set PYTHONIOENCODING=utf-8&& python \"$CLAUDE_PROJECT_DIR/.claude/hooks/pushover-hook/pushover-notify.py\""
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "set PYTHONIOENCODING=utf-8&& python \"$CLAUDE_PROJECT_DIR/.claude/hooks/pushover-hook/pushover-notify.py\""
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "set PYTHONIOENCODING=utf-8&& python \"$CLAUDE_PROJECT_DIR/.claude/hooks/pushover-hook/pushover-notify.py\""
          }
        ]
      }
    ]
  }
}
```

### 通知优先级说明

| 优先级值 | 说明 | 适用场景 |
|----------|------|----------|
| -2 | 最低优先级，静默通知 | 后台任务 |
| -1 | 低优先级 | 信息性消息 |
| 0 | 正常优先级（默认） | 任务完成 |
| 1 | 高优先级 | 需要关注、权限请求 |
| 2 | 紧急，会持续提醒 | 关键错误 |

### Windows 编码注意事项

在 Windows 系统调用脚本时，需设置 `PYTHONIOENCODING=utf-8`：

```json
"command": "set PYTHONIOENCODING=utf-8&& python \"path/to/pushover-notify.py\""
```

或在调用代码中设置：

```python
env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"
subprocess.run(cmd, env=env)
```

---

## 配置选项

### 通知优先级修改

编辑 `pushover-notify.py`，修改 `send_notifications()` 调用时的 `priority` 参数。

### 禁用特定 Hook

编辑 `.claude/settings.json`，删除不需要的 hook 配置。

### 日志管理

- 日志位置：`.claude/hooks/pushover-hook/debug.log`
- 日志轮转：自动保留 3 天
- 历史日志格式：`debug.YYYY-MM-DD.log`

---

## 故障排查

### 诊断工具

```bash
# 运行完整诊断
python .claude/hooks/pushover-hook/diagnose.py

# 查看调试日志
cat .claude/hooks/pushover-hook/debug.log
```

### 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 没有收到通知 | 环境变量未设置 | 检查 `PUSHOVER_TOKEN` 和 `PUSHOVER_USER` |
| 中文乱码 | 编码问题 | 设置 `PYTHONIOENCODING=utf-8` |
| 通知显示 `{}` | 旧版本 bug | 更新到最新版本 |
| Windows 通知不工作 | PowerShell 执行策略 | 检查 BurntToast 模块安装 |

### 手动验证

```bash
# 验证环境变量
echo $PUSHOVER_TOKEN   # Linux/macOS
echo $env:PUSHOVER_TOKEN  # Windows PowerShell

# 验证网络连接
curl -I https://api.pushover.net

# 验证 Python
python --version  # 需要 3.6+
```

---

## 项目结构

```
.claude/
├── hooks/
│   └── pushover-hook/
│       ├── pushover-notify.py    # 主 hook 脚本
│       ├── test-pushover.py      # 测试通知脚本
│       ├── diagnose.py           # 诊断脚本
│       ├── debug.log             # 调试日志（运行时生成）
│       └── README.md             # 详细文档
├── cache/                         # 会话缓存目录（自动清理）
│   └── session-{id}.jsonl
└── settings.json                  # Hook 配置文件
install.py                         # 自动安装脚本
```

---

## 安全说明

- 密钥存储在环境变量中，不写入代码或配置文件
- 对话缓存在任务完成后自动删除
- 通知发送失败不影响应用正常运行

---

## 许可证

MIT License

---

## 贡献

欢迎提交 Issue 和 Pull Request！
