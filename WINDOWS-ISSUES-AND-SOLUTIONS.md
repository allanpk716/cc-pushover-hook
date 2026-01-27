# Windows Hook 配置问题与解决方案

## 问题发现

在 Windows 系统上，hook 配置使用 `python` 命令时无法正常工作。

## 根本原因

### Windows 上的 Python 命令问题

Windows 系统上存在多个 Python 执行器，它们的可靠性各不相同：

1. **`python` 命令** - 不可靠 ⚠️
   - 位置：`C:\Users\{user}\AppData\Local\Microsoft\WindowsApps\python.exe`
   - 问题：这是 Windows Store 创建的 stub 文件
   - 行为：
     - 如果未安装 Python，会打开 Microsoft Store
     - 如果已安装 Python，可能返回错误码 49（不是标准的 0/1）
     - 在某些情况下可能找不到实际的 Python 解释器

2. **`py` 命令** - 推荐 ✅
   - 位置：`C:\Windows\py.exe`
   - 说明：Python Launcher for Windows
   - 优点：
     - 始终可用（Python 安装时自动安装）
     - 自动找到系统中安装的 Python
     - 支持多版本管理
     - 在脚本和自动化场景中更可靠

3. **完整路径** - 可用但不灵活
   - 示例：`C:\Users\{user}\AppData\Local\Programs\Python\Python314\python.exe`
   - 缺点：
     - 路径因用户和版本而异
     - 升级 Python 后需要更新路径
     - 不适合跨机器部署

## 问题表现

### 错误码说明

- **退出码 49**：WindowsApps python.exe 找到有效的 Python 解释器
- **退出码 9009**：命令未找到（CMD 的标准错误码）

### 测试结果

```bash
# 使用 python 命令
python script.py
# 返回：退出码 49 或 9009

# 使用 py 命令
py script.py
# 返回：退出码 0（成功）
```

## 解决方案

### 修改配置文件

将 `.claude/settings.json` 中的所有 `python` 命令改为 `py`：

#### 修改前
```json
{
  "command": "set PYTHONIOENCODING=utf-8&& python \"%CLAUDE_PROJECT_DIR%\\.claude\\hooks\\pushover-hook\\pushover-notify.py\""
}
```

#### 修改后
```json
{
  "command": "set PYTHONIOENCODING=utf-8&& py \"%CLAUDE_PROJECT_DIR%\\.claude\\hooks\\pushover-hook\\pushover-notify.py\""
}
```

### 验证方法

运行测试脚本验证修复：

```bash
.claude\hooks\pushover-hook\test-hook-with-env.bat
```

预期输出：
```
========================================
Simulating Claude Code Hook Execution
========================================
CLAUDE_PROJECT_DIR = C:\WorkSpace\cc-pushover-hook

========================================
Hook command executed with exit code: 0
========================================
```

## 安装脚本更新建议

为了确保新用户自动获得正确的配置，建议更新 `install.py`：

### 检测逻辑

```python
import sys
import subprocess

def get_python_command():
    """获取系统上可靠的 Python 命令"""
    if sys.platform == "win32":
        # Windows: 优先使用 py launcher
        try:
            result = subprocess.run(
                ["py", "--version"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return "py"
        except Exception:
            pass

        # 回退到 python（但可能不可靠）
        return "python"
    else:
        # Linux/Mac: 使用 python3 或 python
        return "python3"

# 使用示例
python_cmd = get_python_command()
command = f'set PYTHONIOENCODING=utf-8&& {python_cmd} "%CLAUDE_PROJECT_DIR%\\.claude\\hooks\\pushover-hook\\pushover-notify.py"'
```

### 跨平台配置

#### Windows
```json
{
  "command": "set PYTHONIOENCODING=utf-8&& py \"%CLAUDE_PROJECT_DIR%\\.claude\\hooks\\pushover-hook\\pushover-notify.py\""
}
```

#### Linux/Mac
```json
{
  "command": "PYTHONIOENCODING=utf-8 python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/pushover-hook/pushover-notify.py\""
}
```

## 其他 Windows 特殊注意事项

### 1. 环境变量设置

Windows BAT 语法中设置环境变量并执行命令的正确方式：

```bat
set VAR=value&& command
```

注意：
- `=` 后面不要有空格
- `&&` 前面不要有空格（因为 `set` 会将空格包含在值中）

### 2. 路径分隔符

- Windows: 使用反斜杠 `\`
- JSON 中需要转义：`\\`
- 或使用正斜杠 `/`（Python 也能正确处理）

### 3. 编码设置

Windows 控制台默认使用系统编码（中文 Windows 是 GBK），可能导致输出乱码。

设置 UTF-8 编码的几种方法：

#### 方法 1：环境变量（推荐）
```bat
set PYTHONIOENCODING=utf-8
```

#### 方法 2：Python 脚本内设置
```python
if hasattr(sys.stdin, 'reconfigure'):
    sys.stdin.reconfigure(encoding='utf-8')
```

#### 方法 3：使用 chcp（不推荐，影响整个进程）
```bat
chcp 65001
```

### 4. 引号处理

JSON 配置中的引号规则：
- JSON 字符串用双引号 `"`
- 路径中的双引号需要转义：`\"`
- 示例：`"command": "py \"%CLAUDE_PROJECT_DIR%\\script.py\""`

## 测试检查清单

在部署前，请确认以下测试都通过：

- [ ] `py --version` 能正常输出版本号
- [ ] `py script.py` 能正常运行脚本
- [ ] 测试脚本 `test-hook-with-env.bat` 返回退出码 0
- [ ] 手动设置环境变量后，脚本能读取到 `CLAUDE_PROJECT_DIR`
- [ ] 日志文件正确生成且包含 UTF-8 字符
- [ ] Pushover 通知能正常发送（如果配置了 token）

## 升级指南

### 对于现有用户

1. 拉取最新代码
2. 手动更新 `.claude/settings.json`，将 `python` 替换为 `py`
3. 或重新运行 `python install.py`（如果已更新安装脚本）
4. 重启 Claude Code

### 验证升级

在 Claude Code 中执行任何命令，观察：
- Pushover 通知是否收到
- 本地 Windows 通知是否弹出
- 日志文件是否正常生成

## 总结

Windows 上的主要问题是 `python` 命令的不可靠性，解决方案是使用 `py` launcher。这是一个简单但重要的修复，能确保 hook 在 Windows 系统上稳定运行。

**关键要点**：
- ✅ Windows 上使用 `py` 命令而非 `python`
- ✅ `py` 是 Python Launcher，更可靠
- ✅ 跨平台配置需要不同的命令
- ✅ 安装脚本应自动检测并使用正确的命令

---

**文档版本**: v1.0
**更新日期**: 2025-01-27
**适用系统**: Windows 10/11
**Python 版本**: 3.14.x（其他版本同样适用）
