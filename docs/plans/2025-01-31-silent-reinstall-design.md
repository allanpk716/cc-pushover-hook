# 静默重装功能设计文档

**日期：** 2025-01-31
**版本：** 1.0.0
**状态：** 已批准

## 目标

为 install.py 添加静默重装功能，使外部项目可以通过简单的命令行参数实现指定项目的 pushover hook 自动更新，无需用户交互。

## 核心设计原则

1. **最小侵入**：基于现有的 `--non-interactive` 和 `--force` 参数，不添加复杂新逻辑
2. **覆盖模式**：静默重装时备份现有配置，然后用新版本完全覆盖
3. **标准输出**：保持现有 JSON 格式输出，便于外部程序解析

## 功能设计

### 命令行接口

**静默重装命令：**

```bash
# 推荐方式（快捷参数）
python install.py --target-dir <项目路径> --reinstall

# 完整参数
python install.py --target-dir <项目路径> --force --non-interactive --quiet
```

**参数说明：**
- `--target-dir PATH`：指定要重装的项目目录（必需）
- `--reinstall`：静默重装快捷方式（等同于 `--force --non-interactive --quiet`）
- `--force`：强制重装，即使检测到已有新版本结构也会执行备份升级
- `--non-interactive`：静默模式，不询问任何确认，所有自动执行
- `--quiet`：减少过程输出，只输出最终 JSON 结果

**行为定义：**

当同时使用 `--force` + `--non-interactive` 时，脚本将：
1. 不显示 ASCII banner
2. 不询问任何确认
3. 自动备份现有配置（生成带时间戳的 backup 文件）
4. 完全覆盖安装新版本
5. 清理旧版本文件
6. 输出标准 JSON 结果

### 返回格式

**成功输出（JSON）：**

```json
{
  "status": "success",
  "action": "backup_and_upgrade",
  "hook_path": "C:\\项目路径\\.claude\\hooks\\pushover-hook",
  "version": "1.0.0"
}
```

**错误输出（JSON）：**

```json
{
  "status": "error",
  "code": 2,
  "message": "Target directory does not exist: /path/to/project"
}
```

### 退出码约定

| 退出码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1 | 一般错误 |
| 2 | 目标目录不存在或不可写 |
| 3 | Python 环境检查失败 |
| 4 | 配置文件备份失败 |
| 5 | Hook 文件复制失败 |

## 实现细节

### 修改点

#### 1. 新增 `--reinstall` 参数

**位置：** `install.py:195-237` (`_create_argument_parser()`)

**修改内容：**
```python
parser.add_argument(
    "--reinstall",
    action="store_true",
    help="Silent reinstall (equivalent to --force --non-interactive --quiet)"
)
```

**处理逻辑：**
```python
# 在 __init__ 或相关位置处理
if self.parsed_args.reinstall:
    self.parsed_args.force = True
    self.parsed_args.non_interactive = True
    self.parsed_args.quiet = True
```

#### 2. 优化 `determine_install_action()`

**位置：** `install.py:150-193`

**确保逻辑：**
- `--force` + `--non-interactive` 组合时明确返回 `backup_and_upgrade`
- 保持现有逻辑不变

#### 3. 静默模式下目录自动创建

**位置：** `install.py:269-342` (`get_target_directory()`)

**修改内容：**
- 静默模式下目录不存在时自动创建，无需询问
- 失败时返回退出码 2

```python
if not target.exists():
    if self.is_non_interactive():
        try:
            target.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(json.dumps({
                "status": "error",
                "code": 2,
                "message": f"Cannot create directory: {e}"
            }))
            sys.exit(2)
    # ... 交互模式逻辑
```

#### 4. 增强环境检查错误处理

**位置：** `install.py:879-942` (`check_environment()`)

**修改内容：**
- 静默模式下 Python 不可用时返回退出码 3
- Pushover 环境变量缺失只警告，不中断

```python
if self.is_non_interactive() and not env_status["python_available"]:
    print(json.dumps({
        "status": "error",
        "code": 3,
        "message": "Python not available"
    }))
    sys.exit(3)
```

#### 5. 备份失败必须中断

**位置：** `install.py:480-500` (`backup_settings()`)

**修改内容：**
- 静默模式下备份失败应中断并返回退出码 4

```python
try:
    # ... 备份逻辑
    return backup_path
except Exception as e:
    if self.is_non_interactive():
        print(json.dumps({
            "status": "error",
            "code": 4,
            "message": f"Failed to backup: {e}"
        }))
        sys.exit(4)
    # ... 交互模式警告
```

#### 6. 文件复制失败返回退出码 5

**位置：** `install.py:364-419` (`copy_hook_files()`)

**修改内容：**
- 统一返回退出码 5

```python
except Exception as e:
    print(json.dumps({
        "status": "error",
        "code": 5,
        "message": f"Failed to copy {filename}: {e}"
    }))
    sys.exit(5)
```

## 测试策略

### 单元测试

- 测试 `--reinstall` 参数解析
- 测试 `determine_install_action()` 在各种参数组合下的返回值
- 测试退出码的正确性

### 集成测试

1. **静默重装全新项目**
2. **静默重装有旧版本的项目**
3. **静默重装有新版本的项目**
4. **目录不存在时的行为**
5. **目录不可写时的行为**
6. **备份失败时的处理**

### 测试命令示例

```bash
# 测试静默重装
python install.py --target-dir "./test-project" --reinstall

# 验证 JSON 输出
python install.py --target-dir "./test-project" --reinstall | jq .

# 测试错误处理
python install.py --target-dir "./non-existent" --reinstall
echo $?
```

## 文档更新

### 新建 INTEGRATION.md

完整的第三方集成指南，包含：
- 概述和前置要求
- 快速开始命令
- 参数说明表
- 输出格式示例
- 退出码说明
- Python 调用示例
- 注意事项

### 更新 README.md

添加"快速集成"章节，链接到 INTEGRATION.md

## 修改文件清单

1. **install.py** - 添加 `--reinstall` 参数，优化错误处理和退出码
2. **INTEGRATION.md** - 新建第三方集成文档
3. **README.md** - 添加集成快速链接

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

1. **备份安全**：重装会自动备份现有配置到 `.claude/settings.json.backup_YYYYMMDD_HHMMSS`
2. **环境变量**：PUSHOVER_TOKEN、PUSHOVER_USER 需要单独配置，不在静默安装范围内
3. **平台兼容性**：Windows 建议使用 `py` 命令启动器，Linux/macOS 使用 `python3`
4. **权限要求**：需要目标目录的写权限
