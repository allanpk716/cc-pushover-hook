# 静默重装功能实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标：** 为 install.py 添加 `--reinstall` 参数，支持第三方项目静默重装 Pushover Hook，无需用户交互。

**架构：** 基于 existing `--force` 和 `--non-interactive` 参数，新增 `--reinstall` 快捷参数，统一错误处理和退出码，保持 JSON 输出格式兼容。

**技术栈：** Python 3.7+, argparse, subprocess, JSON

---

## Task 1: 添加 `--reinstall` 参数

**文件：**
- Modify: `install.py:195-237` (`_create_argument_parser` 方法)

### Step 1: 添加参数定义

在 `_create_argument_parser()` 方法中添加 `--reinstall` 参数：

```python
parser.add_argument(
    "--reinstall",
    action="store_true",
    help="Silent reinstall (equivalent to --force --non-interactive --quiet)"
)
```

**位置：** 在 `--version` 参数之前添加

### Step 2: 处理参数逻辑

在 `Installer.__init__()` 方法末尾（parser.parse_args 之后）添加：

```python
# Handle --reinstall shortcut
if self.parsed_args.reinstall:
    self.parsed_args.force = True
    self.parsed_args.non_interactive = True
    self.parsed_args.quiet = True
```

### Step 3: 测试参数解析

运行测试：
```bash
cd .worktrees/silent-reinstall
python install.py --reinstall --help
```

预期输出：help 中包含 `--reinstall` 选项说明

### Step 4: 提交

```bash
git add install.py
git commit -m "feat(install): add --reinstall shortcut parameter for silent installation"
```

---

## Task 2: 增强静默模式下目录自动创建

**文件：**
- Modify: `install.py:269-342` (`get_target_directory` 方法)

### Step 1: 修改目录不存在的处理逻辑

在 `get_target_directory()` 方法中，找到处理 target 目录不存在的代码（约 line 273-285），修改为：

```python
if not target.exists():
    if self.is_non_interactive():
        # 静默模式：自动创建目录
        try:
            target.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(json.dumps({
                "status": "error",
                "code": 2,
                "message": f"Cannot create directory: {e}"
            }))
            sys.exit(2)
    else:
        # 交互模式：询问用户
        response = input(f"Directory does not exist: {target}\nCreate it? (y/n): ").lower()
        if response == 'y':
            target.mkdir(parents=True, exist_ok=True)
        else:
            sys.exit(1)
```

### Step 2: 测试目录创建

创建测试项目目录：
```bash
# 测试自动创建
python install.py --target-dir "./test-auto-create" --reinstall
# 应该成功创建目录并输出 JSON
```

### Step 3: 提交

```bash
git add install.py
git commit -m "feat(install): auto-create target directory in silent mode with exit code 2"
```

---

## Task 3: 增强 Python 环境检查错误处理

**文件：**
- Modify: `install.py:879-942` (`check_environment` 方法)

### Step 1: 在方法末尾添加静默模式检查

在 `check_environment()` 方法的 `return env_status` 之前添加：

```python
# 静默模式下 Python 不可用应立即失败
if self.is_non_interactive() and not env_status["python_available"]:
    print(json.dumps({
        "status": "error",
        "code": 3,
        "message": "Python not available on this system"
    }))
    sys.exit(3)
```

### Step 2: 测试错误处理（模拟）

注释掉 Python 检查部分的代码，模拟失败场景：

```python
# 临时测试：强制 python_available = False
# env_status["python_available"] = False
```

运行测试：
```bash
python install.py --target-dir "./test-project" --reinstall
# 应该输出 code 3 错误
```

**注意：** 测试后恢复代码

### Step 3: 提交

```bash
git add install.py
git commit -m "feat(install): add exit code 3 for missing Python in silent mode"
```

---

## Task 4: 增强备份失败错误处理

**文件：**
- Modify: `install.py:480-500` (`backup_settings` 方法)

### Step 1: 修改异常处理

将 `backup_settings()` 方法的异常处理部分修改为：

```python
except Exception as e:
    if self.is_non_interactive():
        # 静默模式：备份失败是致命错误
        print(json.dumps({
            "status": "error",
            "code": 4,
            "message": f"Failed to backup settings.json: {e}"
        }))
        sys.exit(4)
    else:
        # 交互模式：仅警告
        self.print_info(f"[WARN] Failed to backup settings.json: {e}")
        return None
```

### Step 2: 测试备份失败处理

手动触发备份失败（临时修改 settings.json 权限或内容），运行：
```bash
python install.py --target-dir "./test-project" --reinstall
# 应该输出 code 4 错误
```

### Step 3: 提交

```bash
git add install.py
git commit -m "feat(install): add exit code 4 for backup failure in silent mode"
```

---

## Task 5: 统一文件复制失败退出码

**文件：**
- Modify: `install.py:364-419` (`copy_hook_files` 方法)

### Step 1: 修改错误处理和退出码

将 `copy_hook_files()` 方法中的异常处理（约 line 402-406）修改为：

```python
except Exception as e:
    print(json.dumps({
        "status": "error",
        "code": 5,
        "message": f"Failed to copy {filename}: {e}"
    }))
    sys.exit(5)
```

同样修改 "No files were copied" 错误（约 line 409-413）：

```python
if copied == 0:
    print(json.dumps({
        "status": "error",
        "code": 5,
        "message": "No files were copied!"
    }))
    sys.exit(5)
```

### Step 2: 测试文件复制失败

临时删除 `hooks/` 目录内容，运行：
```bash
python install.py --target-dir "./test-project" --reinstall
# 应该输出 code 5 错误
```

### Step 3: 提交

```bash
git add install.py
git commit -m "feat(install): add exit code 5 for file copy failures"
```

---

## Task 6: 创建集成文档

**文件：**
- Create: `INTEGRATION.md`

### Step 1: 创建文档文件

创建完整的集成文档 `INTEGRATION.md`：

```markdown
# Pushover Hook 集成指南

## 概述
本文档说明如何在第三方项目中自动集成和更新 Claude Code Pushover Hook。

## 前置要求
- Python 3.7+ 已安装
- 目标项目是 Claude Code 项目（有 .claude 目录）

## 快速开始

### 1. 静默重装命令
\`\`\`bash
# Windows
py install.py --target-dir "C:\path\to\project" --reinstall

# Linux/macOS
python3 install.py --target-dir "/path/to/project" --reinstall
\`\`\`

### 2. 完整安装命令
\`\`\`bash
py install.py --target-dir "C:\path\to\project" --force --non-interactive --quiet
\`\`\`

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
\`\`\`json
{
  "status": "success",
  "action": "backup_and_upgrade",
  "hook_path": "C:\\project\\.claude\\hooks\\pushover-hook",
  "version": "1.0.0"
}
\`\`\`

### 错误输出
\`\`\`json
{
  "status": "error",
  "code": 2,
  "message": "Target directory does not exist"
}
\`\`\`

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
\`\`\`python
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
\`\`\`

## 注意事项
1. 重装会自动备份现有配置到 `.claude/settings.json.backup_YYYYMMDD_HHMMSS`
2. 环境变量（PUSHOVER_TOKEN、PUSHOVER_USER）需要单独配置
3. Windows 建议使用 `py` 命令启动器
```

### Step 2: 提交

```bash
git add INTEGRATION.md
git commit -m "docs: add third-party integration guide for silent installation"
```

---

## Task 7: 更新 README.md

**文件：**
- Modify: `README.md`

### Step 1: 添加快速集成章节

在 README.md 的适当位置（比如安装章节之后）添加：

```markdown
## 快速集成（第三方项目）

如果你想在其他项目中自动集成 Pushover Hook，请参考：

📘 **[完整集成指南](INTEGRATION.md)** - 静默安装、命令行参数、Python 调用示例

**快速开始：**
\`\`\`bash
# 静默重装到指定项目
python install.py --target-dir "/path/to/project" --reinstall
\`\`\`
```

### Step 2: 提交

```bash
git add README.md
git commit -m "docs: add quick integration section to README"
```

---

## Task 8: 端到端测试

### Step 1: 测试全新安装

```bash
# 创建测试项目
mkdir ./test-fresh-install
cd .worktrees/silent-reinstall

# 运行静默安装
python install.py --target-dir "../test-fresh-install" --reinstall
```

预期输出：
- 退出码：0
- JSON 包含 `"status": "success"`
- 验证文件已创建：`../test-fresh-install/.claude/hooks/pushover-hook/`

### Step 2: 测试重装

```bash
# 再次运行（重装）
python install.py --target-dir "../test-fresh-install" --reinstall
```

预期输出：
- 退出码：0
- JSON 包含 `"action": "backup_and_upgrade"`
- 备份文件已创建：`settings.json.backup_YYYYMMDD_HHMMSS`

### Step 3: 测试 JSON 输出格式

```bash
# 解析 JSON 输出
python install.py --target-dir "../test-fresh-install" --reinstall | python -m json.tool
```

预期输出：格式化的 JSON

### Step 4: 测试错误场景

```bash
# 测试不存在的目录
python install.py --target-dir "./non-existent-dir" --reinstall
echo $?
# 预期：退出码 2

# 测试 Python 调用
python -c "
import subprocess
import json
result = subprocess.run(
    ['python', 'install.py', '--target-dir', '../test-fresh-install', '--reinstall'],
    capture_output=True,
    text=True
)
data = json.loads(result.stdout)
print(f'Status: {data[\"status\"]}')
print(f'Version: {data.get(\"version\", \"N/A\")}')
"
```

### Step 5: 清理测试文件

```bash
cd ..
rm -rf ./test-fresh-install
```

### Step 6: 提交（如有测试脚本）

如果创建了测试脚本，提交：
```bash
git add test-scripts/
git commit -m "test: add end-to-end integration tests"
```

---

## Task 9: 代码审查和最终验证

### Step 1: 审查所有修改

```bash
cd .worktrees/silent-reinstall
git diff main..feature/silent-reinstall
```

检查要点：
- ✅ 所有退出码正确使用（0-5）
- ✅ JSON 输出格式一致
- ✅ 静默模式无交互提示
- ✅ 文档完整准确

### Step 2: 运行最后一次完整测试

```bash
# 清理环境
rm -rf ./test-final

# 完整流程测试
python install.py --target-dir "./test-final" --reinstall
echo "Exit code: $?"

# 验证安装
ls ./test-final/.claude/hooks/pushover-hook/
cat ./test-final/.claude/settings.json
```

### Step 3: 创建 Pull Request 准备

```bash
# 推送到远程
git push -u origin feature/silent-reinstall

# PR 描述模板
```

**Pull Request 描述：**

```markdown
## 功能：静默重装支持

### 概述
添加 `--reinstall` 参数，支持第三方项目静默重装 Pushover Hook，无需用户交互。

### 主要改进
1. **新参数 `--reinstall`** - 快捷方式（等同于 --force --non-interactive --quiet）
2. **标准化退出码** - 0（成功）, 2（目录）, 3（Python）, 4（备份）, 5（复制）
3. **增强错误处理** - 静默模式下关键失败立即退出
4. **完整集成文档** - INTEGRATION.md 第三方集成指南

### 使用示例
\`\`\`bash
# 静默重装
python install.py --target-dir "/path/to/project" --reinstall

# Python 调用
subprocess.run(['python', 'install.py', '--target-dir', path, '--reinstall'])
\`\`\`

### 测试
- ✅ 全新安装
- ✅ 重装现有项目
- ✅ 错误处理（目录、Python、备份、复制）
- ✅ JSON 输出格式
- ✅ 跨平台（Windows/Linux）

### 文档
- 📘 INTEGRATION.md - 完整集成指南
- 📝 README.md - 快速集成章节

### 相关设计文档
- docs/plans/2025-01-31-silent-reinstall-design.md
```

### Step 4: 最终提交

```bash
# 如有任何调整，提交
git add .
git commit -m "chore: final adjustments for silent reinstall feature"
```

---

## 实施检查清单

- [ ] Task 1: `--reinstall` 参数添加
- [ ] Task 2: 静默模式目录自动创建
- [ ] Task 3: Python 环境检查错误处理
- [ ] Task 4: 备份失败错误处理
- [ ] Task 5: 文件复制失败退出码
- [ ] Task 6: INTEGRATION.md 文档
- [ ] Task 7: README.md 更新
- [ ] Task 8: 端到端测试
- [ ] Task 9: 代码审查和验证

## 验收标准

1. **功能完整性**
   - ✅ `--reinstall` 参数可用
   - ✅ 静默模式无任何交互
   - ✅ 所有错误场景有正确退出码
   - ✅ JSON 输出格式一致

2. **文档完整性**
   - ✅ INTEGRATION.md 包含所有必要信息
   - ✅ README.md 有集成指引
   - ✅ 代码注释准确

3. **测试覆盖**
   - ✅ 全新安装成功
   - ✅ 重装成功并备份
   - ✅ 错误场景正确处理
   - ✅ 跨平台兼容

4. **代码质量**
   - ✅ 遵循现有代码风格
   - ✅ 无明显重复代码
   - ✅ 错误处理完善

---

## 注意事项

1. **Windows 兼容性**：测试时注意路径分隔符（`\` vs `/`）
2. **权限问题**：确保测试目录有写权限
3. **环境变量**：Pushover TOKEN/USER 不在安装范围内
4. **备份策略**：每次重装都会创建新备份，注意磁盘空间

---

**计划完成时间估计：** 45-60 分钟

**依赖项：** 无

**风险：**
- Windows 特定路径处理需要测试
- 静默模式错误处理需要全面测试
