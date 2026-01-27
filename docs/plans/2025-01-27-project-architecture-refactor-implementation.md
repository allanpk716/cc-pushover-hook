# 项目架构重构实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 重构项目架构，将 `.claude/hooks/` 移到根目录的 `hooks/`，并增强 install.py 的智能检测和升级能力。

**Architecture:** 清晰分离源代码（`hooks/`）和安装目标（`.claude/`），实现智能检测、安全升级、环境检查和跨平台兼容。

**Tech Stack:** Python 3.6+, pathlib, subprocess, json, argparse

---

## 前置准备

### Task 0: 创建 Git Worktree

**目的:** 在隔离的工作环境中进行重构，不影响主分支。

**Step 1: 创建并切换到 worktree**

运行:
```bash
git worktree add ../cc-pushover-hook-refactor main
cd ../cc-pushover-hook-refactor
```

预期: 创建新的 worktree 目录，并切换到该目录

**Step 2: 验证 worktree**

运行:
```bash
git worktree list
pwd
```

预期: 输出显示两个 worktree，当前在 `cc-pushover-hook-refactor` 目录

**Step 3: 创建特性分支**

运行:
```bash
git checkout -b feature/architecture-refactor
```

预期: 输出 "Switched to a new branch 'feature/architecture-refactor'"

**Commit:**
```bash
# 此时无需提交，只是准备工作
```

---

## 阶段 1：文件结构重构

### Task 1: 创建 hooks/ 目录并移动文件

**Files:**
- Create: `hooks/` (目录)
- Move: `.claude/hooks/pushover-hook/*` → `hooks/`

**Step 1: 创建 hooks/ 目录**

运行:
```bash
mkdir hooks
```

预期: 创建 `hooks/` 目录

**Step 2: 移动所有 hook 文件到 hooks/**

运行:
```bash
mv .claude/hooks/pushover-hook/* hooks/
```

预期: 所有文件从 `.claude/hooks/pushover-hook/` 移动到 `hooks/`

**Step 3: 验证文件移动**

运行:
```bash
ls -la hooks/
```

预期输出:
```
pushover-notify.py
test-pushover.py
test-windows-notification.py
diagnose.py
install-burnttoast.ps1
README.md
```

**Step 4: 删除空的 .claude 目录结构**

运行:
```bash
rm -rf .claude/hooks
```

预期: 删除 `.claude/hooks` 目录

**Commit:**
```bash
git add hooks/
git rm -r .claude/hooks/
git commit -m "refactor: move hook files to hooks/ directory"
```

---

### Task 2: 更新 .gitignore

**Files:**
- Modify: `.gitignore`

**Step 1: 添加 .claude/ 到 .gitignore**

运行:
```bash
echo ".claude/" >> .gitignore
```

预期: `.gitignore` 文件末尾添加 `.claude/`

**Step 2: 验证 .gitignore**

运行:
```bash
cat .gitignore | tail -5
```

预期: 看到 `.claude/` 规则

**Commit:**
```bash
git add .gitignore
git commit -m "chore: ignore .claude/ directory in source repo"
```

---

## 阶段 2：install.py 重构 - 检测和决策逻辑

### Task 3: 添加检测现有安装的方法

**Files:**
- Modify: `install.py` (在 `Installer` 类中添加方法)

**Step 1: 在 Installer 类中添加 detect_existing_installation 方法**

在 `install.py` 的 `Installer` 类中添加（在 `__init__` 方法之后）:

```python
def detect_existing_installation(self) -> dict:
    """
    检测目标项目的现有安装状态。

    Returns:
        包含检测结果的字典:
        - has_settings: bool - 是否存在 settings.json
        - has_old_hook: bool - 是否存在旧版本的扁平结构 hook
        - has_new_hook: bool - 是否存在新版本的子目录 hook
        - old_version: str|None - 已安装的版本号
    """
    settings_path = self.target_dir / ".claude" / "settings.json"
    hook_dir = self.target_dir / ".claude" / "hooks"

    detection = {
        "has_settings": settings_path.exists(),
        "has_old_hook": (hook_dir / "pushover-notify.py").exists(),
        "has_new_hook": (hook_dir / "pushover-hook" / "pushover-notify.py").exists(),
        "old_version": self.get_installed_version()
    }

    return detection
```

**Step 2: 添加 get_installed_version 辅助方法**

在 `detect_existing_installation` 方法之后添加:

```python
def get_installed_version(self) -> str:
    """
    从 VERSION 文件读取已安装的版本号。

    Returns:
        版本字符串，如果不存在则返回 None
    """
    version_file = self.target_dir / ".claude" / "hooks" / "pushover-hook" / "VERSION"
    if version_file.exists():
        try:
            with open(version_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith("version="):
                        return line.strip().split("=", 1)[1].strip()
        except Exception:
            pass
    return None
```

**Step 3: 测试语法**

运行:
```bash
python -m py_compile install.py
```

预期: 无语法错误

**Commit:**
```bash
git add install.py
git commit -m "feat: add installation detection methods"
```

---

### Task 4: 添加安装决策逻辑

**Files:**
- Modify: `install.py` (添加决策方法)

**Step 1: 添加 determine_install_action 方法**

在 `get_installed_version` 方法之后添加:

```python
def determine_install_action(self, detection: dict) -> str:
    """
    根据检测结果决定安装行为。

    Args:
        detection: detect_existing_installation() 返回的检测结果

    Returns:
        安装动作类型:
        - "install": 全新安装
        - "merge": 合并到现有配置
        - "migrate": 从旧版本迁移
        - "upgrade": 升级现有安装
    """
    if detection["has_new_hook"]:
        return "upgrade"
    elif detection["has_old_hook"]:
        return "migrate"
    elif detection["has_settings"]:
        return "merge"
    else:
        return "install"
```

**Step 2: 测试语法**

运行:
```bash
python -m py_compile install.py
```

预期: 无语法错误

**Commit:**
```bash
git add install.py
git commit -m "feat: add installation action decision logic"
```

---

### Task 5: 添加配置合并方法

**Files:**
- Modify: `install.py` (添加配置合并方法)

**Step 1: 改进现有的 merge_hook_configs 方法**

找到现有的 `merge_hook_configs` 方法（约在 409-458 行），替换为:

```python
def merge_hook_configs(self, existing_hooks: dict, new_hooks: dict) -> dict:
    """
    智能合并新的 hook 配置到现有配置中。

    策略:
    1. 如果事件不存在，直接添加
    2. 如果事件存在，检测并移除旧的 pushover hook 配置
    3. 添加新的 pushover hook 配置
    4. 保留其他非 pushover 的 hook 配置

    Args:
        existing_hooks: 现有的 hooks 配置字典
        new_hooks: 要合并的新 hooks 配置字典

    Returns:
        合并后的 hooks 配置字典
    """
    merged = existing_hooks.copy()

    for event_name, event_configs in new_hooks.items():
        if event_name not in merged:
            # 事件不存在，直接添加
            merged[event_name] = event_configs
        else:
            # 事件已存在，检查是否需要替换旧的 pushover hook
            for new_event_config in event_configs:
                new_hooks_list = new_event_config.get("hooks", [])
                new_has_pushover = any(
                    "pushover-notify.py" in hook.get("command", "")
                    for hook in new_hooks_list
                )

                if new_has_pushover:
                    # 移除该事件的旧 pushover hook 配置
                    filtered_configs = []
                    removed_count = 0
                    for existing_event_config in merged[event_name]:
                        existing_hooks_list = existing_event_config.get("hooks", [])
                        existing_has_pushover = any(
                            "pushover-notify.py" in hook.get("command", "")
                            for hook in existing_hooks_list
                        )
                        if existing_has_pushover:
                            removed_count += 1
                        else:
                            filtered_configs.append(existing_event_config)

                    merged[event_name] = filtered_configs

                    if removed_count > 0:
                        self.print_info(f"[INFO] 已替换 {removed_count} 个旧版 pushover hook 配置 ({event_name})")

                    # 添加新的配置
                    merged[event_name].append(new_event_config)
                else:
                    # 非 pushover hook，检查是否重复
                    found = False
                    for existing_event_config in merged[event_name]:
                        if existing_event_config.get("hooks") == new_event_config.get("hooks"):
                            found = True
                            break

                    if not found:
                        merged[event_name].append(new_event_config)
                    else:
                        self.print_info(f"[INFO] Hook 已存在，跳过 ({event_name})")

    return merged
```

**Step 2: 测试语法**

运行:
```bash
python -m py_compile install.py
```

预期: 无语法错误

**Commit:**
```bash
git add install.py
git commit -m "refactor: improve hook config merging logic"
```

---

## 阶段 3：自动升级和备份机制

### Task 6: 添加备份和清理旧文件的方法

**Files:**
- Modify: `install.py` (添加备份和清理方法)

**Step 1: 改进 backup_settings 方法**

找到现有的 `backup_settings` 方法（约在 397-407 行），确保它接受 `settings_path` 参数:

```python
def backup_settings(self, settings_path: Path) -> None:
    """
    创建现有 settings.json 的备份。

    Args:
        settings_path: settings.json 文件路径
    """
    try:
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = settings_path.parent / f"settings.json.backup_{timestamp}"

        shutil.copy2(settings_path, backup_path)

        self.print_info(f"[OK] 已备份配置: {backup_path.name}")
    except Exception as e:
        self.print_info(f"[WARN] 备份失败: {e}")
```

**Step 2: 改进 cleanup_old_files 方法**

找到现有的方法（在 `copy_hook_files` 中），提取为独立方法:

```python
def cleanup_old_files(self) -> None:
    """
    清理旧版本的 hook 文件。

    删除旧版本（扁平结构）的文件和目录。
    """
    old_hooks_dir = self.target_dir / ".claude" / "hooks"

    # 旧版本扁平结构的文件
    old_files = [
        "pushover-notify.py",
        "test-pushover.py",
        "diagnose.py",
        "README.md",
        "debug.log"
    ]

    removed_count = 0
    for filename in old_files:
        old_file = old_hooks_dir / filename
        if old_file.exists():
            try:
                if old_file.is_dir():
                    shutil.rmtree(old_file)
                else:
                    old_file.unlink()
                self.print_info(f"[OK] 已删除旧文件: {filename}")
                removed_count += 1
            except Exception as e:
                self.print_info(f"[WARN] 删除失败 {filename}: {e}")

    # 清理 __pycache__
    pycache = old_hooks_dir / "__pycache__"
    if pycache.exists() and pycache.is_dir():
        try:
            shutil.rmtree(pycache)
            self.print_info(f"[OK] 已删除: __pycache__")
        except Exception as e:
            self.print_info(f"[WARN] 删除 __pycache__ 失败: {e}")

    if removed_count == 0:
        self.print_info("[INFO] 未找到旧版本文件")
```

**Step 3: 测试语法**

运行:
```bash
python -m py_compile install.py
```

预期: 无语法错误

**Commit:**
```bash
git add install.py
git commit -m "refactor: extract and improve cleanup logic"
```

---

### Task 7: 更新 copy_hook_files 方法以使用新路径

**Files:**
- Modify: `install.py` (修改 `copy_hook_files` 方法)

**Step 1: 修改源代码目录路径**

找到 `copy_hook_files` 方法（约在 268-358 行），修改 `source_hooks_dir` 的定义:

将:
```python
source_hooks_dir = self.script_dir / ".claude" / "hooks" / "pushover-hook"
```

改为:
```python
source_hooks_dir = self.script_dir / "hooks"
```

**Step 2: 测试语法**

运行:
```bash
python -m py_compile install.py
```

预期: 无语法错误

**Commit:**
```bash
git add install.py
git commit -m "refactor: update hook source path to hooks/ directory"
```

---

### Task 8: 实现不同的安装模式

**Files:**
- Modify: `install.py` (添加新的安装模式方法)

**Step 1: 添加 fresh_install 方法**

在 `copy_hook_files` 方法之后添加:

```python
def fresh_install(self) -> None:
    """
    全新安装模式。
    创建目录结构，复制文件，生成配置。
    """
    self.print_info("\n[模式] 全新安装")

    self.create_hook_directory()
    self.copy_hook_files()
    self.create_version_file()
    self.generate_settings_json()
```

**Step 2: 添加 migrate_from_old_version 方法**

在 `fresh_install` 方法之后添加:

```python
def migrate_from_old_version(self) -> None:
    """
    从旧版本迁移模式。
    清理旧文件，安装新版本，更新配置。
    """
    self.print_info("\n[模式] 版本迁移")

    # 清理旧文件
    self.cleanup_old_files()

    # 安装新版本
    self.create_hook_directory()
    self.copy_hook_files()
    self.create_version_file()

    # 生成或合并配置
    settings_path = self.target_dir / ".claude" / "settings.json"
    if settings_path.exists():
        self.backup_settings(settings_path)
        self.merge_settings_and_generate()
    else:
        self.generate_settings_json()
```

**Step 3: 添加 backup_and_upgrade 方法**

在 `migrate_from_old_version` 方法之后添加:

```python
def backup_and_upgrade(self, detection: dict) -> None:
    """
    备份并升级模式。
    备份现有配置，更新 hook 文件，合并配置。
    """
    self.print_info(f"\n[模式] 版本升级 ({detection['old_version']} → {self.version})")

    settings_path = self.target_dir / ".claude" / "settings.json"

    # 备份配置
    if detection["has_settings"]:
        self.backup_settings(settings_path)

    # 更新文件
    self.copy_hook_files()
    self.create_version_file()

    # 合并配置
    self.merge_settings_and_generate()
```

**Step 4: 添加 merge_to_existing_settings 方法**

在 `backup_and_upgrade` 方法之后添加:

```python
def merge_to_existing_settings(self) -> None:
    """
    合并到现有配置模式。
    保留现有配置，添加 pushover hook。
    """
    self.print_info("\n[模式] 配置合并")

    self.create_hook_directory()
    self.copy_hook_files()
    self.create_version_file()
    self.merge_settings_and_generate()
```

**Step 5: 添加 merge_settings_and_generate 辅助方法**

在 `merge_to_existing_settings` 方法之后添加:

```python
def merge_settings_and_generate(self) -> None:
    """
    合并现有配置并生成新的 settings.json。
    """
    settings_path = self.target_dir / ".claude" / "settings.json"

    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            existing_settings = json.load(f)

        # 生成新的 pushover hook 配置
        hook_script_path = self.hook_dir / "pushover-notify.py"

        if self.platform == "Windows":
            command = f'set PYTHONIOENCODING=utf-8&& python "{hook_script_path}"'
        else:
            command = f'PYTHONIOENCODING=utf-8 "{hook_script_path}"'

        pushover_hooks = {
            "UserPromptSubmit": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": command,
                            "timeout": self.parsed_args.timeout
                        }
                    ]
                }
            ],
            "Stop": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": command,
                            "timeout": self.parsed_args.timeout
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
                            "command": command,
                            "timeout": self.parsed_args.timeout
                        }
                    ]
                }
            ]
        }

        # 合并配置
        existing_hooks = existing_settings.get("hooks", {})
        merged_hooks = self.merge_hook_configs(existing_hooks, pushover_hooks)

        existing_settings["hooks"] = merged_hooks

        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(existing_settings, f, indent=2, ensure_ascii=False)

        self.print_info(f"[OK] 已合并 pushover hook 配置")

    except json.JSONDecodeError as e:
        if self.is_non_interactive():
            print(json.dumps({
                "status": "error",
                "message": f"现有 settings.json 无效: {e}"
            }))
        else:
            print(f"[ERROR] 现有 settings.json 无效: {e}")
        sys.exit(1)
    except Exception as e:
        if self.is_non_interactive():
            print(json.dumps({
                "status": "error",
                "message": f"合并配置失败: {e}"
            }))
        else:
            print(f"[ERROR] 合并配置失败: {e}")
        sys.exit(1)
```

**Step 6: 测试语法**

运行:
```bash
python -m py_compile install.py
```

预期: 无语法错误

**Commit:**
```bash
git add install.py
git commit -m "feat: add installation mode methods (install/upgrade/migrate/merge)"
```

---

## 阶段 4：环境变量和依赖检测

### Task 9: 添加环境检测方法

**Files:**
- Modify: `install.py` (添加环境检测方法)

**Step 1: 添加 check_environment 方法**

在 `merge_settings_and_generate` 方法之后添加:

```python
def check_environment(self) -> dict:
    """
    检查环境配置和依赖。

    Returns:
        包含检测结果的字典:
        - pushover_token: bool - 是否设置 PUSHOVER_TOKEN
        - pushover_user: bool - 是否设置 PUSHOVER_USER
        - python_version: bool - Python 版本是否 >= 3.6
        - windows_burnttoast: bool|None - Windows BurntToast 模块（仅 Windows）
    """
    checks = {
        "pushover_token": os.getenv("PUSHOVER_TOKEN") is not None,
        "pushover_user": os.getenv("PUSHOVER_USER") is not None,
        "python_version": sys.version_info >= (3, 6),
    }

    if self.platform == "Windows":
        checks["windows_burnttoast"] = self._check_burnttoast()

    return checks
```

**Step 2: 添加 _check_burnttoast 辅助方法**

在 `check_environment` 方法之后添加:

```python
def _check_burnttoast(self) -> bool:
    """
    检查 Windows BurntToast PowerShell 模块是否已安装。

    Returns:
        True 如果模块已安装，否则 False
    """
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-Module -ListAvailable BurntToast"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False
```

**Step 3: 测试语法**

运行:
```bash
python -m py_compile install.py
```

预期: 无语法错误

**Commit:**
```bash
git add install.py
git commit -m "feat: add environment checking methods"
```

---

### Task 10: 添加环境状态显示方法

**Files:**
- Modify: `install.py` (添加环境状态显示方法)

**Step 1: 添加 show_environment_status 方法**

在 `_check_burnttoast` 方法之后添加:

```python
def show_environment_status(self, checks: dict, interactive: bool) -> None:
    """
    根据模式显示环境配置状态。

    Args:
        checks: check_environment() 返回的检测结果
        interactive: 是否为交互模式
    """
    if interactive:
        self._show_environment_interactive(checks)
    else:
        self._show_environment_json(checks)
```

**Step 2: 添加 _show_environment_interactive 辅助方法**

在 `show_environment_status` 方法之后添加:

```python
def _show_environment_interactive(self, checks: dict) -> None:
    """
    交互模式：显示友好的环境状态提示。
    """
    self.print_info("\n[环境检查]")

    # 检查环境变量
    if checks["pushover_token"] and checks["pushover_user"]:
        self.print_info("[OK] Pushover 环境变量已配置")
    else:
        self.print_info("[WARN] Pushover 环境变量未设置")
        if not checks["pushover_token"]:
            self.print_info("  - PUSHOVER_TOKEN 未设置")
        if not checks["pushover_user"]:
            self.print_info("  - PUSHOVER_USER 未设置")

    # 检查 Python 版本
    if checks["python_version"]:
        self.print_info(f"[OK] Python 版本: {sys.version.split()[0]}")
    else:
        self.print_info(f"[WARN] Python 版本过低: {sys.version.split()[0]} (需要 >= 3.6)")

    # Windows 特定检查
    if self.platform == "Windows":
        if checks.get("windows_burnttoast"):
            self.print_info("[OK] BurntToast 模块已安装")
        else:
            self._show_windows_dependency_guide()
```

**Step 3: 添加 _show_environment_json 辅助方法**

在 `_show_environment_interactive` 方法之后添加:

```python
def _show_environment_json(self, checks: dict) -> None:
    """
    非交互模式：输出 JSON 格式的环境状态。
    """
    result = {
        "status": "success",
        "environment": {
            "pushover_token": checks["pushover_token"],
            "pushover_user": checks["pushover_user"],
            "python_version": checks["python_version"],
            "python_version_string": sys.version.split()[0]
        }
    }

    if self.platform == "Windows":
        result["environment"]["windows_burnttoast"] = checks.get("windows_burnttoast")

    # 添加配置指引
    missing = []
    if not checks["pushover_token"]:
        missing.append("PUSHOVER_TOKEN")
    if not checks["pushover_user"]:
        missing.append("PUSHOVER_USER")

    if missing or (self.platform == "Windows" and not checks.get("windows_burnttoast")):
        result["warnings"] = []
        if missing:
            result["warnings"].append({
                "type": "missing_env_vars",
                "variables": missing,
                "instructions": self.get_env_setup_instructions()
            })
        if self.platform == "Windows" and not checks.get("windows_burnttoast"):
            result["warnings"].append({
                "type": "missing_dependency",
                "dependency": "BurntToast",
                "instructions": "以管理员身份运行 PowerShell，执行: Install-Module -Name BurntToast -Force"
            })

    print(json.dumps(result, indent=2, ensure_ascii=False))
```

**Step 4: 添加 _show_windows_dependency_guide 辅助方法**

在 `_show_environment_json` 方法之后添加:

```python
def _show_windows_dependency_guide(self) -> None:
    """
    显示 Windows BurntToast 依赖安装指引。
    """
    self.print_info("\n[INFO] Windows 本地通知需要安装 BurntToast 模块")
    self.print_info("[INFO] 运行以下命令安装：")
    self.print_info()
    self.print_info("   # 以管理员身份运行 PowerShell")
    self.print_info("   Install-Module -Name BurntToast -Force")
    self.print_info()
    self.print_info("或运行:")
    self.print_info(f"   powershell -ExecutionPolicy Bypass -File \"{self.hook_dir}/install-burnttoast.ps1\"")
```

**Step 5: 测试语法**

运行:
```bash
python -m py_compile install.py
```

预期: 无语法错误

**Commit:**
```bash
git add install.py
git commit -m "feat: add environment status display methods"
```

---

## 阶段 5：集成到主流程

### Task 11: 重构主 run 方法

**Files:**
- Modify: `install.py` (重构 `run` 方法)

**Step 1: 找到并替换 run 方法**

找到现有的 `run` 方法（约在 649-686 行），替换为:

```python
def run(self) -> None:
    """
    运行完整的安装流程。
    """
    try:
        # 1. 显示横幅
        self.print_banner()

        # 2. 获取目标目录
        self.target_dir = self.get_target_directory()

        # 3. 智能检测现有安装
        detection = self.detect_existing_installation()
        action = self.determine_install_action(detection)

        # 4. 执行相应的安装/升级操作
        if action == "install":
            self.fresh_install()
        elif action == "upgrade":
            self.backup_and_upgrade(detection)
        elif action == "migrate":
            self.migrate_from_old_version()
        elif action == "merge":
            self.merge_to_existing_settings()

        # 5. 环境检查
        checks = self.check_environment()
        self.show_environment_status(checks, not self.is_non_interactive())

        # 6. 验证安装（可选）
        if not self.parsed_args.skip_diagnostics and not self.is_non_interactive():
            self.run_verification()

        # 7. 输出完成信息
        self.print_completion_message()

        # 非交互模式输出 JSON 结果
        if self.is_non_interactive():
            result = {
                "status": "success",
                "action": action,
                "hook_path": str(self.hook_dir),
                "version": self.version
            }
            print(json.dumps(result, indent=2, ensure_ascii=False))

    except KeyboardInterrupt:
        if self.is_non_interactive():
            print(json.dumps({"status": "cancelled", "message": "安装已取消"}))
        else:
            print("\n\n[INFO] 安装已取消")
        sys.exit(0)

    except Exception as e:
        self.handle_error(e)
```

**Step 2: 添加 print_completion_message 方法**

在 `run` 方法之后添加:

```python
def print_completion_message(self) -> None:
    """
    显示安装完成信息。
    """
    if self.is_non_interactive():
        return

    print("\n" + "=" * 60)
    print("安装完成！")
    print("=" * 60)
    print(f"\nHook 版本: {self.version}")
    print(f"Hook 路径: {self.hook_dir}")
    print("\n下一步:")
    print("1. 设置环境变量 PUSHOVER_TOKEN 和 PUSHOVER_USER")
    print("2. 运行测试:")
    print(f"   python {self.hook_dir}/test-pushover.py")
```

**Step 3: 添加 handle_error 方法**

在 `print_completion_message` 方法之后添加:

```python
def handle_error(self, error: Exception) -> None:
    """
    统一的错误处理。

    Args:
        error: 捕获的异常对象
    """
    if self.is_non_interactive():
        # JSON 格式错误输出
        error_result = {
            "status": "error",
            "error_type": type(error).__name__,
            "message": str(error)
        }
        print(json.dumps(error_result, indent=2, ensure_ascii=False))
    else:
        # 友好的错误消息
        print(f"\n[ERROR] {error}")
        if hasattr(self, 'parsed_args') and getattr(self.parsed_args, 'debug', False):
            import traceback
            traceback.print_exc()

    sys.exit(1)
```

**Step 4: 测试语法**

运行:
```bash
python -m py_compile install.py
```

预期: 无语法错误

**Commit:**
```bash
git add install.py
git commit -m "refactor: integrate new installation flow into run() method"
```

---

## 阶段 6：清理和优化

### Task 12: 移除调试代码

**Files:**
- Modify: `install.py` (移除调试输出)

**Step 1: 移除 __init__ 中的调试输出**

找到 `__init__` 方法中的调试代码（约在 90-97 行），删除以下行:

```python
# Debug: print received args
import sys
print(f"[DEBUG] sys.argv: {sys.argv}", file=sys.stderr)
print(f"[DEBUG] args parameter: {args}", file=sys.stderr)

# Debug: print parsed args
print(f"[DEBUG] parsed_args.target_dir: {self.parsed_args.target_dir}", file=sys.stderr)
print(f"[DEBUG] parsed_args.non_interactive: {self.parsed_args.non_interactive}", file=sys.stderr)
```

**Step 2: 测试语法**

运行:
```bash
python -m py_compile install.py
```

预期: 无语法错误

**Commit:**
```bash
git add install.py
git commit -m "chore: remove debug output from __init__"
```

---

### Task 13: 更新文档字符串

**Files:**
- Modify: `install.py` (更新模块文档)

**Step 1: 更新模块文档字符串**

修改文件顶部的文档字符串（约在 1-23 行），更新为:

```python
"""
Cross-platform installer for Claude Code Pushover notification hook.

Usage:
    python install.py [OPTIONS]

Options:
    -t, --target-dir PATH    Target project directory
    --force                  Force reinstall, overwrite existing files
    --non-interactive        Non-interactive mode, output JSON results
    --skip-diagnostics       Skip post-install diagnostics
    --quiet                  Quiet mode, reduce output
    --timeout SECONDS        Hook execution timeout in seconds (default: 5)
    --version                Show version information

The script will:
1. Detect your platform (Windows/Linux/macOS)
2. Detect existing installation and determine action:
   - Fresh install: No existing configuration
   - Merge: Existing settings.json, add pushover hooks
   - Migrate: Old version detected, clean up and upgrade
   - Upgrade: New version detected, backup and upgrade
3. Copy all necessary files from hooks/ to target .claude/hooks/pushover-hook/
4. Generate or merge platform-specific settings.json
5. Check environment configuration
6. Run diagnostics to verify installation (unless --skip-diagnostics)
"""
```

**Step 2: 测试语法**

运行:
```bash
python -m py_compile install.py
```

预期: 无语法错误

**Commit:**
```bash
git add install.py
git commit -m "docs: update module docstring with new features"
```

---

## 阶段 7：测试和验证

### Task 14: 在当前项目测试安装

**目的:** 验证安装脚本在源项目本身能正常工作。

**Step 1: 安装到当前项目**

运行:
```bash
python install.py --target-dir . --non-interactive
```

预期输出:
```json
{
  "status": "success",
  "action": "install",
  "hook_path": "C:\\WorkSpace\\cc-pushover-hook\\.claude\\hooks\\pushover-hook",
  "version": "1.1.0"
}
```

**Step 2: 验证文件结构**

运行:
```bash
ls -la .claude/hooks/pushover-hook/
```

预期: 列出所有 hook 文件（pushover-notify.py, test-pushover.py 等）

**Step 3: 验证 settings.json**

运行:
```bash
cat .claude/settings.json
```

预期: 包含 pushover hooks 配置

**Step 4: 清理（为后续测试准备）**

运行:
```bash
rm -rf .claude/
```

预期: 删除安装的文件

**Commit:**
```bash
# 测试成功，无需提交
```

---

### Task 15: 创建临时测试项目并测试升级流程

**目的:** 验证升级和备份机制。

**Step 1: 创建临时测试目录**

运行:
```bash
cd ..
mkdir test-project-v1
cd test-project-v1
```

预期: 创建并切换到测试目录

**Step 2: 手动创建旧版本安装结构**

运行:
```bash
mkdir -p .claude/hooks
cat > .claude/settings.json << 'EOF'
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "set PYTHONIOENCODING=utf-8&& python \".claude/hooks/pushover-notify.py\""
          }
        ]
      }
    ]
  }
}
EOF
```

预期: 创建旧版本的配置

**Step 3: 返回源项目并运行升级**

运行:
```bash
cd ../cc-pushover-hook-refactor
python install.py --target-dir ../test-project-v1 --non-interactive
```

预期输出:
```json
{
  "status": "success",
  "action": "migrate",
  "hook_path": "...",
  "version": "1.1.0"
}
```

**Step 4: 验证备份文件**

运行:
```bash
ls ../test-project-v1/.claude/*.backup*
```

预期: 找到备份文件

**Step 5: 验证新配置**

运行:
```bash
cat ../test-project-v1/.claude/settings.json
```

预期: 配置已更新

**Step 6: 清理测试目录**

运行:
```bash
rm -rf ../test-project-v1
```

预期: 删除测试目录

**Commit:**
```bash
# 测试成功，无需提交
```

---

## 阶段 8：文档更新

### Task 16: 更新 README.md

**Files:**
- Modify: `README.md`

**Step 1: 更新快速开始部分**

找到 "## 快速开始" 部分（约在 34-76 行），更新为:

```markdown
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

# 3. 按照提示设置环境变量

# 4. 发送测试通知
python .claude/hooks/pushover-hook/test-pushover.py
```

### 安装模式

安装脚本会自动检测目标项目的状态并选择适当的安装模式：

- **全新安装**: 目标项目没有任何 pushover 配置
- **配置合并**: 目标项目已有 settings.json，合并 pushover hook
- **版本迁移**: 检测到旧版本结构，自动清理并升级
- **版本升级**: 检测到新版本结构，备份配置并升级

所有升级操作都会自动备份现有配置，支持安全回滚。
```

**Step 2: 更新项目结构部分**

找到 "## 项目结构" 部分（约在 424-439 行），更新为:

```markdown
## 项目结构

### 源项目

```
cc-pushover-hook/
├── hooks/                          # 源代码目录
│   ├── pushover-notify.py          # 主 hook 脚本
│   ├── test-pushover.py            # 测试脚本
│   ├── diagnose.py                 # 诊断脚本
│   └── README.md
├── install.py                      # 安装脚本
└── README.md
```

### 安装后的目标项目

```
target-project/
├── .claude/
│   ├── hooks/
│   │   └── pushover-hook/
│   │       ├── pushover-notify.py  # 从 hooks/ 复制
│   │       ├── VERSION             # 版本信息
│   │       └── README.md
│   ├── cache/                      # 会话缓存
│   └── settings.json               # Hook 配置
└── ... (项目原有文件)
```
```

**Commit:**
```bash
git add README.md
git commit -m "docs: update README with new architecture and installation modes"
```

---

### Task 17: 更新 CHANGELOG.md

**Files:**
- Modify: `CHANGELOG.md`

**Step 1: 添加新版本条目**

在文件顶部添加:

```markdown
## [1.1.0] - 2025-01-27

### Added

- **架构重构**: 源代码移至 `hooks/` 目录，与安装目标 `.claude/` 分离
- **智能安装**: 自动检测现有安装，选择合适的安装模式
- **安装模式**:
  - 全新安装 (install)
  - 配置合并 (merge)
  - 版本迁移 (migrate)
  - 版本升级 (upgrade)
- **自动备份**: 升级时自动备份 settings.json
- **环境检测**: 检查环境变量和系统依赖
- **跨平台优化**: 改进 Windows/Linux/macOS 兼容性
- **非交互模式**: 输出 JSON 格式结果，便于脚本集成

### Changed

- 源代码结构从 `.claude/hooks/pushover-hook/` 改为 `hooks/`
- 安装目标保持为 `.claude/hooks/pushover-hook/`

### Fixed

- 修复旧版本升级时的文件清理问题
- 修复配置合并时的重复 hook 问题
```

**Commit:**
```bash
git add CHANGELOG.md
git commit -m "docs: add v1.1.0 changelog entry"
```

---

## 阶段 9：最终验证和清理

### Task 18: 最终完整性测试

**目的:** 验证所有功能正常工作。

**Step 1: 运行完整安装测试**

运行:
```bash
python install.py --non-interactive --target-dir /tmp/test-final
```

预期: 成功安装，输出 JSON 结果

**Step 2: 验证所有文件**

运行:
```bash
ls /tmp/test-final/.claude/hooks/pushover-hook/
cat /tmp/test-final/.claude/settings.json
cat /tmp/test-final/.claude/hooks/pushover-hook/VERSION
```

预期: 所有文件存在且内容正确

**Step 3: 测试升级**

运行:
```bash
python install.py --non-interactive --target-dir /tmp/test-final
```

预期: 识别为升级模式，创建备份

**Step 4: 清理**

运行:
```bash
rm -rf /tmp/test-final
```

**Commit:**
```bash
# 测试成功，准备合并
```

---

### Task 19: 代码审查和优化

**目的:** 最终代码审查，确保质量。

**Step 1: 检查代码风格**

运行:
```bash
python -m pylint install.py --max-line-length=100
```

预期: 查看是否有严重问题

**Step 2: 检查所有方法是否都有文档字符串**

手动检查 `install.py`，确保所有公共方法都有 `"""docstring"""`

**Step 3: 验证所有 commit 消息**

运行:
```bash
git log --oneline -20
```

预期: commit 消息清晰且遵循约定

**Commit:**
```bash
# 如有小的优化，进行额外提交
```

---

### Task 20: 合并到主分支

**目的:** 将重构完成的工作合并回主分支。

**Step 1: 切换回主分支**

运行:
```bash
cd ../cc-pushover-hook
git checkout main
```

预期: 切换到主分支

**Step 2: 合并特性分支**

运行:
```bash
git merge feature/architecture-refactor --no-ff
```

预期: 成功合并，可能有冲突需要解决

**Step 3: 删除 worktree**

运行:
```bash
git worktree remove ../cc-pushover-hook-refactor
git branch -d feature/architecture-refactor
```

预期: 删除 worktree 和特性分支

**Step 4: 推送到远程**

运行:
```bash
git push origin main
```

预期: 推送到远程仓库

**Step 5: 创建发布标签**

运行:
```bash
git tag -a v1.1.0 -m "Release v1.1.0: Architecture refactor and smart installation"
git push origin v1.1.0
```

预期: 创建并推送标签

**Commit:**
```bash
# 合并完成，准备发布
```

---

## 总结

本实施计划包含 20 个任务，涵盖：

1. **文件结构重构** (Task 1-2): hooks/ 目录创建和 .gitignore 更新
2. **智能检测** (Task 3-5): 现有安装检测和决策逻辑
3. **自动升级** (Task 6-8): 备份、清理和多模式安装
4. **环境检测** (Task 9-10): 环境变量和依赖检查
5. **流程集成** (Task 11-13): 主流程重构和清理
6. **测试验证** (Task 14-15): 安装和升级测试
7. **文档更新** (Task 16-17): README 和 CHANGELOG
8. **最终发布** (Task 18-20): 完整性测试和合并

每个任务都包含详细的步骤、命令和预期输出，确保实施过程清晰可控。
