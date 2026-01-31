# Pushover Hook 集成指南

## 概述
本文档说明如何在第三方项目中自动集成和更新 Claude Code Pushover Hook。

## 前置要求
- Python 3.7+ 已安装
- 目标项目是 Claude Code 项目（有 .claude 目录）

## 快速开始

### 1. 静默重装命令
```bash
# Windows
py install.py --target-dir "C:\path\to\project" --reinstall

# Linux/macOS
python3 install.py --target-dir "/path/to/project" --reinstall
```

### 2. 完整安装命令
```bash
py install.py --target-dir "C:\path\to\project" --force --non-interactive --quiet
```

## 命令参数说明
| 参数 | 说明 |
|------|------|
| `--target-dir PATH` | 目标项目目录（必需） |
| `--reinstall` | 静默重装快捷方式（等同于 --force --non-interactive --quiet） |
| `--force` | 强制重装，覆盖现有文件 |
| `--non-interactive` | 静默模式，无用户交互 |
| `--quiet` | 减少输出，仅显示结果 |

## 输出格式

### 成功输出
```json
{
  "status": "success",
  "action": "backup_and_upgrade",
  "hook_path": "C:\\project\\.claude\\hooks\\pushover-hook",
  "version": "1.0.0"
}
```

### 错误输出
```json
{
  "status": "error",
  "code": 2,
  "message": "Target directory does not exist"
}
```

## 退出码
| 退出码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1 | 一般错误 |
| 2 | 目录不存在或不可写 |
| 3 | Python 环境检查失败 |
| 4 | 配置备份失败 |
| 5 | 文件复制失败 |

## Python 调用示例
```python
import subprocess
import json

def install_pushover_hook(project_path: str) -> bool:
    """静默安装 Pushover Hook 到指定项目"""
    result = subprocess.run(
        ["py", "install.py", "--target-dir", project_path, "--reinstall"],
        capture_output=True,
        text=True,
        cwd="C:\\path\\to\\cc-pushover-hook"
    )

    if result.returncode == 0:
        data = json.loads(result.stdout)
        print(f"安装成功: {data['version']}")
        print(f"Hook 路径: {data['hook_path']}")
        return True
    else:
        try:
            error = json.loads(result.stdout)
            print(f"安装失败 (代码 {error['code']}): {error['message']}")
        except:
            print(f"安装失败: {result.stdout}")
        return False

# 使用示例
success = install_pushover_hook(r"C:\MyProject")
```

## 注意事项
1. 重装会自动备份现有配置到 `.claude/settings.json.backup_YYYYMMDD_HHMMSS`
2. 环境变量（PUSHOVER_TOKEN、PUSHOVER_USER）需要单独配置
3. Windows 建议使用 `py` 命令启动器
