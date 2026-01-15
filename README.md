# Claude Code Pushover 通知 Hook

为 Claude Code 添加 Pushover 通知功能，在任务完成或需要人工干预时发送通知到你的设备。

## 功能特性

- **任务完成通知** - Claude Code 完成任务响应时自动发送通知
- **需要关注通知** - 需要权限请求或等待输入时发送高优先级通知
- **AI 任务摘要** - 使用 Claude CLI 自动生成任务摘要
- **跨平台支持** - 支持 Windows、Linux 和 macOS
- **降级策略** - CLI 调用失败时自动降级

## 前置要求

- Python 3.6+
- Claude Code CLI
- curl（Windows 10+、Linux、macOS 通常已内置）

## 安装步骤

### 1. 获取 Pushover 凭证

1. 访问 [Pushover.net](https://pushover.net/) 注册账号
2. 访问 [Applications](https://pushover.net/apps/build) 创建一个应用
3. 记录 **API Token**（应用密钥）
4. 在你的账户页面记录 **User Key**（用户密钥）

### 2. 设置环境变量

将以下环境变量添加到你的系统配置中：

**Windows (PowerShell):**
```powershell
$env:PUSHOVER_TOKEN="your_api_token_here"
$env:PUSHOVER_USER="your_user_key_here"
```

**Windows (系统环境变量):**
1. 右键"此电脑" -> "属性" -> "高级系统设置"
2. 点击"环境变量"
3. 添加新的用户变量：
   - `PUSHOVER_TOKEN` = your_api_token_here
   - `PUSHOVER_USER` = your_user_key_here

**Linux/macOS:**
```bash
export PUSHOVER_TOKEN="your_api_token_here"
export PUSHOVER_USER="your_user_key_here"
```

要永久保存，添加到 `~/.bashrc` 或 `~/.zshrc`：
```bash
echo 'export PUSHOVER_TOKEN="your_api_token_here"' >> ~/.bashrc
echo 'export PUSHOVER_USER="your_user_key_here"' >> ~/.bashrc
```

### 3. 安装 Hook

#### 方法一：使用自动安装脚本（推荐）

在项目根目录运行安装脚本：

```bash
python install.py
```

安装脚本会：
- 自动检测你的操作系统（Windows/Linux/macOS）
- 询问目标项目路径
- 复制所有必要文件
- 生成适合你系统的 settings.json
- 引导你完成环境变量设置
- 运行诊断验证安装

#### 方法二：手动安装

将以下文件复制到你的项目目录：

```bash
# 复制整个 .claude 目录到你的项目根目录
cp -r .claude /path/to/your/project/
```

**项目结构：**
```
your-project/
├── .claude/
│   ├── hooks/
│   │   ├── pushover-notify.py
│   │   ├── test-pushover.py
│   │   ├── diagnose.py
│   │   └── README.md
│   ├── cache/
│   └── settings.json
└── README.md
```

### 4. 设置执行权限（Linux/macOS）

```bash
chmod +x .claude/hooks/*.py
```

### 5. 验证安装

**运行诊断脚本：**

```bash
python .claude/hooks/diagnose.py
```

**发送测试通知：**

```bash
python .claude/hooks/test-pushover.py
```

### 6. 手动测试（可选）

手动测试 hook 是否正常工作：

**Windows (PowerShell):**
```powershell
# 使用你当前项目的实际路径
'{"hook_event_name":"Stop","session_id":"test123","cwd":"C:\WorkSpace\YourProject"}' | python .claude\hooks\pushover-notify.py
```

**Windows (CMD):**
```cmd
echo {"hook_event_name":"Stop","session_id":"test123","cwd":"C:\WorkSpace\YourProject"} | python .claude\hooks\pushover-notify.py
```

**Linux/macOS:**
```bash
echo '{"hook_event_name":"Stop","session_id":"test123","cwd":"/path/to/project"}' | \
  .claude/hooks/pushover-notify.py
```

你应该在 Pushover 上收到一条测试通知。

## 使用方法

安装完成后，hook 会自动在以下场景发送通知：

### 场景 1: 任务完成

当 Claude Code 完成一个任务并停止响应时，你会收到类似这样的通知：

```
[cc-pushover-hook] Task Complete
Session: abc123def456
Summary: Implemented user authentication feature
```

### 场景 2: 需要关注

当 Claude Code 需要你的人工干预时，你会收到高优先级通知：

```
[cc-pushover-hook] Attention Needed
Session: abc123def456
Type: permission_prompt
Run command: npm install
```

## 配置选项

### 修改通知优先级

编辑 `.claude/hooks/pushover-notify.py`，修改 `priority` 参数：

| 优先级 | 说明 |
|--------|------|
| -2 | 最低优先级，静默通知 |
| -1 | 低优先级 |
| 0 | 正常优先级（默认） |
| 1 | 高优先级（需要关注通知使用） |
| 2 | 紧急，会持续提醒 |

### 禁用特定通知

编辑 `.claude/settings.json`，删除不需要的 hook 配置：

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pushover-notify.py"
          }
        ]
      }
    ]
    // 只保留 Stop 通知，移除其他
  }
}
```

## 故障排查

### 没有收到通知

**使用诊断脚本快速排查：**

```bash
python .claude/hooks/diagnose.py
```

诊断脚本会检查：
- 环境变量是否设置
- Python 是否可用
- Hook 脚本是否存在
- Settings 配置是否正确

**手动检查清单：**

1. **环境变量是否正确设置**
   ```bash
   # Windows
   echo $env:PUSHOVER_TOKEN
   echo $env:PUSHOVER_USER

   # Linux/macOS
   echo $PUSHOVER_TOKEN
   echo $PUSHOVER_USER
   ```

2. **发送测试通知**
   ```bash
   python .claude/hooks/test-pushover.py
   ```

3. **查看调试日志**
   ```bash
   cat .claude/hooks/debug.log
   ```

4. **Token 和 User Key 是否有效**
   - 登录 Pushover.net 确认凭证
   - 尝试重新生成凭证

5. **网络连接是否正常**
   ```bash
   curl -I https://api.pushover.net
   ```

### 摘要生成失败

如果通知显示的是原始用户消息而不是 AI 摘要：

1. **检查 Claude CLI 是否安装**
   ```bash
   claude --version
   ```

2. **检查 CLI 是否在 PATH 中**
   ```bash
   which claude  # Linux/macOS
   where claude  # Windows
   ```

3. **查看 CLI 配置是否正确**
   ```bash
   claude auth status
   ```

### 缓存文件未清理

如果 `.claude/cache/` 目录残留文件：

**Linux/macOS:**
```bash
rm -rf .claude/cache/*
```

**Windows:**
```powershell
Remove-Item -Recurse -Force .claude\cache\*
```

## 安全说明

- **密钥安全**：Pushover 凭证存储在环境变量中，不会写入代码或配置文件
- **缓存清理**：对话缓存在任务完成后自动删除
- **静默失败**：通知发送失败不会影响 Claude Code 正常运行

## 项目文件说明

```
.claude/
├── hooks/
│   ├── pushover-notify.py    # 主 hook 脚本
│   ├── test-pushover.py      # 测试通知脚本
│   ├── diagnose.py           # 诊断脚本
│   ├── debug.log             # 调试日志（运行时生成）
│   └── README.md             # 详细文档
├── cache/                     # 会话缓存目录（自动清理）
│   └── session-{id}.jsonl     # 会话缓存文件
└── settings.json              # Hook 配置文件
install.py                     # 自动安装脚本
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
