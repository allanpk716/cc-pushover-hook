# Claude Code Pushover Notifications 设计文档

**日期:** 2025-01-15
**作者:** Claude
**状态:** 设计完成

---

## 一、功能概述

为 Claude Code 添加 Pushover 通知功能，在以下情况发送通知到用户设备：

1. **任务完成** - Claude Code 完成一次任务响应并停止时
2. **需要关注** - Claude Code 需要人工干预时（权限请求、等待输入）

通知内容包括项目名称、会话 ID、任务摘要（AI 自动生成）和通知详情。

---

## 二、架构设计

### 核心组件

```
┌─────────────────┐
│  Claude Code    │
│   (主进程)       │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│         Hook 系统                │
├─────────────────────────────────┤
│ • UserPromptSubmit Hook          │
│ • Stop Hook                      │
│ • Notification Hook              │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│   pushover-notify.py             │
├─────────────────────────────────┤
│ • 记录用户输入到缓存              │
│ • 读取缓存并调用 Claude CLI      │
│ • 生成任务摘要                   │
│ • 发送 Pushover 通知             │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Pushover API   │
└─────────────────┘
```

### 技术栈

| 组件 | 技术 |
|------|------|
| Hook 脚本 | Python 3 |
| CLI 调用 | Claude Code (-p 模式) |
| 通知发送 | curl + Pushover API |
| 跨平台支持 | Python + subprocess |

---

## 三、Hook 配置

### 配置文件位置

- 项目级: `.claude/settings.json`
- 用户级: `~/.claude/settings.json`

### 完整配置

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pushover-notify.py"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pushover-notify.py"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "permission_prompt|idle_prompt",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pushover-notify.py"
          }
        ]
      }
    ]
  }
}
```

---

## 四、通知脚本实现

### 文件结构

```
.claude/
├── hooks/
│   └── pushover-hook/
│       └── pushover-notify.py
├── cache/
│   └── session-{id}.jsonl
└── settings.json
```

### 核心功能

#### 1. send_pushover()
发送 Pushover 通知，使用 curl 调用 API。

#### 2. get_project_name()
从工作目录路径提取项目名称。

#### 3. summarize_conversation()
- 读取缓存文件中的对话历史
- 调用 `claude -p` 生成摘要
- 失败时降级到提取最后一条用户消息

#### 4. main()
处理三种 hook 事件：
- `UserPromptSubmit`: 记录用户输入
- `Stop`: 发送任务完成通知并清理缓存
- `Notification`: 发送需要关注通知

---

## 五、数据流

### UserPromptSubmit 流程

```
用户提交输入
    ↓
Hook 触发
    ↓
读取 stdin (JSON)
    ↓
提取 prompt 内容
    ↓
追加到 session-{id}.jsonl
```

### Stop 流程

```
Claude 完成响应
    ↓
Hook 触发
    ↓
读取缓存文件
    ↓
调用 claude -p 生成摘要
    ↓
构建通知消息
    ↓
发送 Pushover 通知
    ↓
清理缓存文件
```

### Notification 流程

```
需要权限/输入
    ↓
Hook 触发
    ↓
提取通知详情
    ↓
发送 Pushover 通知 (实时)
```

---

## 六、降级策略

| 场景 | 降级方案 |
|------|----------|
| Claude CLI 未安装 | 提取最后一条用户消息 |
| CLI 调用超时 | 使用降级摘要 |
| Pushover API 失败 | 静默失败，不影响 hook |
| 缓存文件损坏 | 忽略损坏部分 |

---

## 七、环境变量

| 变量 | 说明 | 获取方式 |
|------|------|----------|
| `PUSHOVER_TOKEN` | Pushover App Token | https://pushover.net/apps |
| `PUSHOVER_USER` | Pushover User Key | https://pushover.net/ |

---

## 八、安装步骤

1. 获取 Pushover 凭证
2. 设置环境变量 `PUSHOVER_TOKEN` 和 `PUSHOVER_USER`
3. 创建 `.claude/hooks/pushover-hook/` 和 `.claude/cache/` 目录
4. 添加 `pushover-notify.py` 脚本到 `pushover-hook/` 子目录
5. 设置脚本执行权限 (Linux/macOS)
6. 配置 `.claude/settings.json`
7. 添加 `.claude/cache/` 到 `.gitignore`

---

## 九、跨平台支持

| 平台 | 支持状态 | 说明 |
|------|----------|------|
| Windows | ✅ | Python + curl (Win10+ 内置) |
| Linux | ✅ | Python + curl |
| macOS | ✅ | Python + curl |

---

## 十、安全考虑

1. **密钥存储** - 使用环境变量，不写入配置文件
2. **缓存清理** - 任务完成后自动删除敏感对话记录
3. **错误处理** - 失败时静默处理，不泄露信息
4. **权限控制** - Hook 脚本只读取必要数据

---

## 十一、测试验证

### 手动测试

```bash
echo '{"hook_event_name":"Stop","session_id":"test123","cwd":"/path/to/project"}' | \
  .claude/hooks/pushover-notify.py
```

### 验证清单

- [ ] 环境变量已设置
- [ ] 脚本有执行权限
- [ ] hooks 配置正确
- [ ] Pushover 通知正常接收
- [ ] 摘要生成正常工作
- [ ] 降级方案有效

---

## 十二、故障排查

| 问题 | 检查项 |
|------|--------|
| 无通知 | 环境变量、Token 有效性、网络 |
| 摘要失败 | Claude CLI 安装、网络、API 配额 |
| 缓存残留 | 目录权限、脚本执行权限 |

---

## 十三、未来改进

1. 支持更多通知渠道（Telegram、Discord）
2. 可配置的通知优先级
3. 通知分组和去重
4. 自定义通知模板
5. 统计和分析面板
