# Claude Code Hook 相对路径改进方案

## 改进概述

将 `cc-pushover-hook` 项目中的 hook 配置从**绝对路径**改为使用 **`$CLAUDE_PROJECT_DIR` 环境变量**的相对路径,提高项目的可移植性和灵活性。

## 改进内容

### 修改前 (绝对路径)

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "set PYTHONIOENCODING=utf-8&& python \"C:\\WorkSpace\\agent\\cc-pushover-hook\\.claude\\hooks\\pushover-hook\\pushover-notify.py\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

**问题:**
- ❌ 路径硬编码,只能在特定位置工作
- ❌ 项目移动或复制到其他位置需要手动修改
- ❌ 不同机器上的路径可能不同
- ❌ 不便于团队协作和分享

### 修改后 (使用环境变量)

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "set PYTHONIOENCODING=utf-8&& python \"%CLAUDE_PROJECT_DIR%\\.claude\\hooks\\pushover-hook\\pushover-notify.py\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

**优势:**
- ✅ 项目可以在任意位置工作
- ✅ 无需修改配置即可复制到新位置
- ✅ 跨机器兼容,团队成员可直接使用
- ✅ 符合 Claude Code 官方最佳实践

## 官方文档支持

根据 Claude Code 官方 Hook 文档:

> **Project-Specific Hook Scripts**
>
> You can use the environment variable `CLAUDE_PROJECT_DIR` (only available when Claude Code spawns the hook command) to reference scripts stored in your project, ensuring they work regardless of Claude's current directory.

文档还在 **Security Best Practices** 中明确推荐:

> **Use absolute paths** - Specify full paths for scripts (use `$CLAUDE_PROJECT_DIR` for the project path)

## 工作原理

1. **环境变量自动设置**
   - 当 Claude Code 启动时,会自动设置 `CLAUDE_PROJECT_DIR` 环境变量
   - 该变量指向项目根目录(运行 `claude` 命令的目录)

2. **Hook 执行时**
   - Claude Code 在执行 hook 命令时会将 `CLAUDE_PROJECT_DIR` 注入到命令的环境中
   - hook 命令可以使用 `%CLAUDE_PROJECT_DIR%` (Windows) 或 `$CLAUDE_PROJECT_DIR` (Unix) 引用项目路径

3. **路径解析**
   - `%CLAUDE_PROJECT_DIR%\\.claude\\hooks\\pushover-hook\\pushover-notify.py`
   - 会被解析为完整路径,例如: `C:\WorkSpace\cc-pushover-hook\.claude\hooks\pushover-hook\pushover-notify.py`

## 测试验证

### 创建的测试脚本

1. **test-env-path.bat** - Windows 批处理测试脚本
   - 验证环境变量是否正确设置
   - 检查相对路径是否能正确解析到脚本
   - 运行: `.claude\hooks\pushover-hook\test-env-path.bat`

2. **test-env-path.py** - Python 测试脚本
   - 提供更详细的路径验证
   - 支持手动测试模式 (`--manual` 参数)
   - 运行: `python .claude\hooks\pushover-hook\test-env-path.py --manual`

3. **test-hook-with-env.bat** - Hook 执行模拟测试
   - 模拟 Claude Code 的 hook 调用
   - 验证完整的命令执行流程
   - 运行: `.claude\hooks\pushover-hook\test-hook-with-env.bat`

### 测试结果

所有测试脚本均通过验证:
- ✅ 环境变量正确设置
- ✅ 相对路径能正确解析
- ✅ Hook 脚本能被找到
- ✅ 路径配置符合预期

## 部署说明

### 对于现有用户升级

1. 运行安装脚本:
   ```bash
   python install.py
   ```

2. 安装脚本会自动更新 `settings.json` 中的路径配置

3. 重启 Claude Code 以使更改生效

### 手动更新步骤

如果需要手动更新:

1. 打开 `.claude/settings.json`
2. 将所有的绝对路径 `C:\...\cc-pushover-hook\...` 替换为 `%CLAUDE_PROJECT_DIR%\...`
3. 保存文件
4. 重启 Claude Code

## 兼容性

### Windows
使用 `%CLAUDE_PROJECT_DIR%` 语法:
```json
"command": "python \"%CLAUDE_PROJECT_DIR%\\.claude\\hooks\\pushover-hook\\pushover-notify.py\""
```

### Linux/Mac
使用 `$CLAUDE_PROJECT_DIR` 语法:
```json
"command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/pushover-hook/pushover-notify.py\""
```

## 注意事项

1. **环境变量只在 hook 执行时可用**
   - `CLAUDE_PROJECT_DIR` 只在 Claude Code 执行 hook 命令时设置
   - 手动运行脚本时需要自己设置该变量

2. **引号的使用**
   - 在 JSON 中使用 `\"` 转义双引号
   - 路径中包含空格时必须使用引号

3. **调试**
   - 使用 `claude --debug` 查看详细的 hook 执行信息
   - 检查 `.claude/hooks/pushover-hook/debug.log` 了解 hook 运行情况

## 影响范围

此次改进影响以下 hook 事件:
- **UserPromptSubmit** - 用户提交提示时触发
- **Stop** - Claude Code 完成响应时触发
- **Notification** - 发送通知时触发

所有这些事件都已更新为使用相对路径配置。

## 总结

通过使用 `$CLAUDE_PROJECT_DIR` 环境变量,`cc-pushover-hook` 项目现在具有更好的可移植性和灵活性。用户可以自由地移动项目位置、在不同机器上部署,而无需修改配置文件。这完全符合 Claude Code 官方推荐的最佳实践。

---

**改进版本**: v2.0
**改进日期**: 2025-01-27
**改进内容**: 使用 CLAUDE_PROJECT_DIR 环境变量替代绝对路径
