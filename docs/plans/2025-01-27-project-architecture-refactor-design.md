# 项目架构重构设计文档

**日期**: 2025-01-27
**作者**: Claude Code
**状态**: 设计阶段

---

## 目录

- [概述](#概述)
- [目标](#目标)
- [新架构设计](#新架构设计)
- [install.py 核心逻辑](#installpy-核心逻辑)
- [自动升级和备份机制](#自动升级和备份机制)
- [环境变量和依赖的智能处理](#环境变量和依赖的智能处理)
- [平台兼容性和命令生成](#平台兼容性和命令生成)
- [实施计划](#实施计划)

---

## 概述

本文档描述了 cc-pushover-hook 项目的架构重构方案。主要目标是将 `.claude/hooks/` 目录移到项目根目录，使源代码结构更清晰，并增强 `install.py` 的智能判断能力。

### 当前问题

1. **源代码和安装目标混淆**：`.claude/` 既是源代码目录，也是安装目标目录
2. **测试不便**：修改代码后需要区分是修改源代码还是修改安装后的文件
3. **升级体验差**：无法自动检测和升级旧版本
4. **环境配置不完善**：缺乏智能的环境变量和依赖检测

---

## 目标

1. **清晰的架构分离**：源代码在 `hooks/`，安装目标在 `.claude/`
2. **智能安装/升级**：自动检测现有安装，智能决定安装策略
3. **安全的升级机制**：自动备份，支持回滚
4. **友好的环境配置**：交互模式引导，非交互模式机器可读
5. **跨平台兼容**：正确处理 Windows/Linux/macOS 的差异

---

## 新架构设计

### 源项目结构

```
cc-pushover-hook/
├── hooks/                          # 源代码目录（扁平结构）
│   ├── pushover-notify.py          # 主 hook 脚本
│   ├── test-pushover.py            # Pushover 测试脚本
│   ├── test-windows-notification.py # Windows 通知测试
│   ├── diagnose.py                 # 诊断脚本
│   ├── install-burnttoast.ps1      # Windows 依赖安装
│   └── README.md                   # Hook 详细文档
├── install.py                      # 智能安装脚本
├── README.md                       # 项目文档
├── CHANGELOG.md                    # 变更日志
├── CLAUDE.md                       # 开发规则
└── .gitignore                      # 忽略 .claude/ 目录
```

### 安装后的目标项目结构

```
target-project/
├── .claude/
│   ├── hooks/
│   │   └── pushover-hook/
│   │       ├── pushover-notify.py  # 从 hooks/ 复制
│   │       ├── test-pushover.py
│   │       ├── diagnose.py
│   │       ├── VERSION             # 版本信息文件
│   │       └── README.md
│   ├── cache/                      # 会话缓存目录
│   └── settings.json               # Hook 配置（合并或新建）
└── ... (项目原有文件)
```

### 关键设计决策

1. **源项目与安装目标分离**：
   - `hooks/` 是源代码目录
   - `.claude/` 是安装目标目录（在源项目中通过 `.gitignore` 忽略）

2. **删除源项目的 `.claude/`**：
   - 通过 `.gitignore` 忽略 `.claude/` 目录
   - 测试时运行 `python install.py --target-dir .` 安装到当前项目

3. **扁平结构**：
   - `hooks/` 直接包含所有文件，便于维护
   - 安装时复制到 `.claude/hooks/pushover-hook/` 子目录

---

## install.py 核心逻辑

### 智能检测功能

```python
class Installer:
    def detect_existing_installation(self):
        """检测现有安装"""
        settings_path = self.target_dir / ".claude" / "settings.json"
        hook_dir = self.target_dir / ".claude" / "hooks"

        detection = {
            "has_settings": settings_path.exists(),
            "has_old_hook": (hook_dir / "pushover-notify.py").exists(),
            "has_new_hook": (hook_dir / "pushover-hook" / "pushover-notify.py").exists(),
            "old_version": self.get_installed_version()
        }
        return detection

    def get_installed_version(self):
        """从 VERSION 文件读取已安装版本"""
        version_file = self.target_dir / ".claude" / "hooks" / "pushover-hook" / "VERSION"
        if version_file.exists():
            with open(version_file) as f:
                for line in f:
                    if line.startswith("version="):
                        return line.strip().split("=")[1]
        return None
```

### 安装决策逻辑

```python
def determine_install_action(self, detection):
    """根据检测结果决定安装行为"""
    if detection["has_new_hook"]:
        return "upgrade"      # 已有新版本，升级
    elif detection["has_old_hook"]:
        return "migrate"      # 旧版本，迁移并升级
    elif detection["has_settings"]:
        return "merge"        # 有配置但无 hook，合并配置
    else:
        return "install"      # 全新安装
```

### 四种安装模式

1. **全新安装 (install)**：
   - 创建 `.claude/hooks/pushover-hook/` 目录
   - 复制所有文件
   - 创建新的 `settings.json`

2. **配置合并 (merge)**：
   - 保留现有 `settings.json`
   - 合并 pushover hook 配置
   - 添加 hook 文件

3. **版本迁移 (migrate)**：
   - 删除旧版本扁平结构的文件
   - 安装新版本到子目录
   - 更新 `settings.json` 中的命令路径

4. **版本升级 (upgrade)**：
   - 备份现有配置
   - 更新 hook 文件
   - 合并配置（保留用户修改）

### 配置合并策略

```python
def merge_hook_configs(self, existing_hooks, new_hooks):
    """智能合并 hook 配置"""
    merged = existing_hooks.copy()

    for event_name, event_configs in new_hooks.items():
        if event_name not in merged:
            merged[event_name] = event_configs
        else:
            # 检测并移除旧的 pushover hook
            for new_event_config in event_configs:
                new_has_pushover = any(
                    "pushover-notify.py" in hook.get("command", "")
                    for hook in new_event_config.get("hooks", [])
                )

                if new_has_pushover:
                    # 移除旧配置
                    filtered_configs = [
                        cfg for cfg in merged[event_name]
                        if not any("pushover-notify.py" in h.get("command", "")
                                  for h in cfg.get("hooks", []))
                    ]
                    merged[event_name] = filtered_configs
                    merged[event_name].append(new_event_config)

    return merged
```

---

## 自动升级和备份机制

### 版本比较和备份

```python
def backup_and_upgrade(self, detection):
    """备份现有配置并升级"""
    settings_path = self.target_dir / ".claude" / "settings.json"

    # 1. 备份 settings.json
    if detection["has_settings"]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = settings_path.parent / f"settings.json.backup_{timestamp}"
        shutil.copy2(settings_path, backup_path)
        self.print_info(f"[OK] 已备份配置: {backup_path.name}")

    # 2. 清理旧文件
    self.cleanup_old_files(detection)

    # 3. 安装新文件
    self.install_hooks()

    # 4. 合并配置
    self.merge_or_create_settings()
```

### 旧文件清理

```python
def cleanup_old_files(self, detection):
    """清理旧版本的文件"""
    old_hooks_dir = self.target_dir / ".claude" / "hooks"

    # 旧版本（扁平结构）的文件
    old_files = [
        "pushover-notify.py",
        "test-pushover.py",
        "diagnose.py",
        "README.md",
        "debug.log"
    ]

    for filename in old_files:
        old_file = old_hooks_dir / filename
        if old_file.exists():
            old_file.unlink()
            self.print_info(f"[OK] 已删除旧文件: {filename}")

    # 清理 __pycache__
    pycache = old_hooks_dir / "__pycache__"
    if pycache.exists():
        shutil.rmtree(pycache)
```

### VERSION 文件格式

```
version=1.1.0
installed_at=2025-01-27T15:30:00Z
git_commit=fa065e9764738c31cf1f7437cea76c0d824bec00
```

### 升级日志

每次升级都会：
1. 创建带时间戳的备份文件 (`settings.json.backup_YYYYMMDD_HHMMSS`)
2. 记录版本变更到 `VERSION` 文件
3. 显示升级前后的版本信息
4. 支持手动回滚（恢复备份文件）

---

## 环境变量和依赖的智能处理

### 环境检测逻辑

```python
def check_environment(self):
    """检查环境配置和依赖"""
    checks = {
        "pushover_token": os.getenv("PUSHOVER_TOKEN") is not None,
        "pushover_user": os.getenv("PUSHOVER_USER") is not None,
        "python_version": sys.version_info >= (3, 6),
        "windows_burnttoast": self.check_burnttoast() if self.platform == "Windows" else None
    }
    return checks

def check_burnttoast(self):
    """检查 Windows BurntToast 模块"""
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-Module -ListAvailable BurntToast"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except:
        return False
```

### 智能混合响应

```python
def show_environment_status(self, checks, interactive):
    """根据模式显示环境状态"""

    if interactive:
        # 交互模式：友好的提示 + 可选设置
        if not checks["pushover_token"]:
            response = input("PUSHOVER_TOKEN 未设置，是否现在设置？ (y/n): ")
            if response.lower() == 'y':
                self.interactive_setup_env()
        else:
            self.print_info("[OK] 环境变量已配置")
    else:
        # 非交互模式：JSON 格式输出
        result = {
            "status": "warning",
            "environment": {
                "pushover_token": checks["pushover_token"],
                "pushover_user": checks["pushover_user"],
                "windows_burnttoast": checks.get("windows_burnttoast")
            },
            "instructions": self.get_env_setup_instructions()
        }
        print(json.dumps(result, indent=2))
```

### Windows 依赖引导

```python
def show_windows_dependency_guide(self):
    """显示 Windows 依赖安装指引"""
    if not self.check_burnttoast():
        self.print_info("[INFO] Windows 本地通知需要安装 BurntToast 模块")
        self.print_info("[INFO] 运行以下命令安装：")
        self.print_info()
        self.print_info("   # 以管理员身份运行 PowerShell")
        self.print_info("   Install-Module -Name BurntToast -Force")
        self.print_info()
        self.print_info("或运行:")
        self.print_info(f"   powershell -ExecutionPolicy Bypass -File \"{self.hook_dir}/install-burnttoast.ps1\"")
```

### 设计要点

1. **交互模式**：友好引导，可选择是否设置
2. **非交互模式**：JSON 格式输出，便于脚本解析
3. **不强制设置**：仅检测和提示，不阻止安装
4. **提供具体指引**：告诉用户如何安装缺失的依赖

---

## 平台兼容性和命令生成

### 跨平台命令生成

```python
def generate_hook_command(self):
    """根据平台生成正确的 hook 命令"""
    hook_script_path = self.hook_dir / "pushover-notify.py"

    if self.platform == "Windows":
        # Windows: 需要设置编码并使用正确的路径引号
        command = f'set PYTHONIOENCODING=utf-8&& python "{hook_script_path}"'
    else:
        # Unix/Linux/macOS: 直接执行
        command = f'PYTHONIOENCODING=utf-8 "{hook_script_path}"'

    return command
```

### 路径处理

```python
def resolve_target_directory(self, target_input):
    """智能解析目标目录路径"""
    target = Path(target_input).resolve()

    # 处理 Windows 路径的特殊情况
    if self.platform == "Windows":
        # 支持正斜杠和反斜杠
        target = Path(target_input.replace('/', '\\')).resolve()

    # 验证目录可写性
    if not self.is_writable(target):
        raise InstallationError(f"目录不可写: {target}")

    return target
```

### install.py 的主要流程

```python
def run(self):
    """主安装流程"""
    try:
        # 1. 显示横幅
        self.print_banner()

        # 2. 获取目标目录
        self.target_dir = self.get_target_directory()

        # 3. 智能检测现有安装
        detection = self.detect_existing_installation()
        action = self.determine_install_action(detection)

        # 4. 执行安装/升级
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
        self.show_environment_status(checks, self.is_interactive())

        # 6. 验证安装（可选）
        if not self.parsed_args.skip_diagnostics:
            self.run_verification()

        # 7. 输出结果
        self.print_completion_message()

    except Exception as e:
        self.handle_error(e)
```

### 错误处理

```python
def handle_error(self, error):
    """统一错误处理"""
    if self.is_non_interactive():
        # JSON 格式错误输出
        error_result = {
            "status": "error",
            "error_type": type(error).__name__,
            "message": str(error)
        }
        print(json.dumps(error_result))
    else:
        # 友好的错误消息
        print(f"\n[ERROR] {error}")
        if self.parsed_args.debug:
            import traceback
            traceback.print_exc()

    sys.exit(1)
```

---

## 实施计划

### 阶段 1：文件结构重构
1. 创建 `hooks/` 目录
2. 移动 `.claude/hooks/pushover-hook/` 中的所有文件到 `hooks/`
3. 删除源项目的 `.claude/` 目录
4. 更新 `.gitignore` 忽略 `.claude/`

### 阶段 2：install.py 重构
1. 添加 `detect_existing_installation()` 方法
2. 实现 `determine_install_action()` 逻辑
3. 添加 `merge_hook_configs()` 方法
4. 实现备份和升级机制

### 阶段 3：环境检测
1. 实现 `check_environment()` 方法
2. 添加 Windows BurntToast 检测
3. 实现交互式和非交互式环境引导
4. 更新文档

### 阶段 4：测试和验证
1. 在全新项目上测试安装
2. 在已有配置的项目上测试合并
3. 在旧版本项目上测试升级
4. 验证备份和回滚机制
5. 跨平台测试（Windows/Linux/macOS）

### 阶段 5：文档更新
1. 更新 README.md
2. 更新 CHANGELOG.md
3. 添加迁移指南
4. 更新示例和截图

---

## 总结

本次重构实现了：

1. **清晰的架构分离**：源代码和安装目标明确分开
2. **智能安装/升级**：自动检测现有安装，智能决定安装策略
3. **安全的升级机制**：自动备份，支持回滚
4. **友好的环境配置**：交互模式引导，非交互模式机器可读
5. **跨平台兼容**：正确处理 Windows/Linux/macOS 的差异

这些改进将显著提升项目的可维护性和用户体验。
