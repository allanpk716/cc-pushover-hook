#!/usr/bin/env python3
"""
Cross-platform installer for Claude Code Pushover notification hook.

This intelligent installer supports multiple installation scenarios:
- Fresh install: New installation with no existing configuration
- Migration: Upgrade from old flat structure to new subdirectory structure
- Upgrade: Backup and upgrade existing installation
- Merge: Merge Pushover hooks into existing settings.json

Usage:
    python install.py [OPTIONS]

Options:
    -t, --target-dir PATH    Target project directory (required for non-interactive mode)
    --force                  Force reinstall, overwrite existing files
    --non-interactive        Non-interactive mode, don't ask for confirmation
    --skip-diagnostics       Skip post-install diagnostics
    --quiet                  Quiet mode, reduce output
    --timeout SECONDS        Hook execution timeout in seconds (default: 5)
    --version                Show version information

The script will:
1. Detect your platform (Windows/Linux/macOS)
2. Ask for the target project directory (or use --target-dir)
3. Auto-detect existing installation and determine best action:
   - Fresh install if no existing configuration
   - Migrate from old version (flat -> subdirectory) if detected
   - Backup and upgrade if new version structure exists
   - Merge to existing settings.json if other hooks present
4. Copy all necessary files to .claude/hooks/pushover-hook/
5. Automatically cleanup old files from previous versions
6. Generate platform-specific settings.json with proper paths
7. Create VERSION file with installation metadata
8. Guide you through environment variable setup
9. Run diagnostics to verify installation (unless --skip-diagnostics)

Version Information:
- Uses git tags/describe for dynamic versioning
- Creates VERSION file with version, install time, and git commit
- Supports upgrade detection and migration between versions
"""

import os
import shutil
import sys
import json
import argparse
import subprocess
from pathlib import Path
from platform import system


class Installer:
    """Cross-platform installer for Pushover hook."""

    VERSION = "1.0.0"

    def get_version_from_git(self) -> str:
        """
        Get version from git tags.

        Returns:
            Version string from git describe, or commit hash, or fallback VERSION
        """
        try:
            # Try git describe --tags --always first
            result = subprocess.run(
                ['git', 'describe', '--tags', '--always'],
                cwd=self.script_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()

            # Fallback to git rev-parse --short HEAD
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                cwd=self.script_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass

        # Ultimate fallback to hardcoded VERSION
        return self.VERSION

    def __init__(self, args=None):
        self.platform = system()
        self.script_dir = Path(__file__).parent.resolve()
        self.target_dir = None
        self.hook_dir = None
        self.args = args

        # Parse command line arguments
        self.parser = self._create_argument_parser()
        self.parsed_args = self.parser.parse_args(args)

        # Set version after script_dir is initialized
        self.version = self.get_version_from_git()

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

    def determine_install_action(self, detection: dict) -> str:
        """
        根据检测结果确定安装策略。

        Args:
            detection: detect_existing_installation() 的返回值

        Returns:
            安装策略字符串:
            - 'fresh_install': 全新安装，没有现有配置
            - 'migrate_from_old': 从旧版本迁移（扁平结构 -> 子目录结构）
            - 'backup_and_upgrade': 备份并升级（已有新版本结构）
            - 'merge_to_existing': 合并到现有 settings.json
            - 'merge_settings_only': 仅合并配置（文件已存在）
        """
        has_settings = detection["has_settings"]
        has_old_hook = detection["has_old_hook"]
        has_new_hook = detection["has_new_hook"]
        old_version = detection["old_version"]

        # 强制重新安装
        if self.parsed_args.force:
            if has_new_hook:
                return 'backup_and_upgrade'
            return 'fresh_install'

        # 已有新版本结构
        if has_new_hook:
            if has_settings:
                return 'merge_to_existing'
            return 'merge_settings_only'

        # 有旧版本结构
        if has_old_hook:
            if has_settings:
                return 'migrate_from_old'
            return 'fresh_install'

        # 只有 settings.json，没有 hook 文件
        if has_settings:
            return 'merge_to_existing'

        # 完全全新安装
        return 'fresh_install'

    def _create_argument_parser(self):
        """Create command line argument parser."""
        parser = argparse.ArgumentParser(
            description="Install Claude Code Pushover notification hook",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        parser.add_argument(
            "-t", "--target-dir",
            type=str,
            help="Target project directory (required for non-interactive mode)"
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force reinstall, overwrite existing files"
        )
        parser.add_argument(
            "--non-interactive",
            action="store_true",
            help="Non-interactive mode, don't ask for confirmation"
        )
        parser.add_argument(
            "--skip-diagnostics",
            action="store_true",
            help="Skip post-install diagnostics"
        )
        parser.add_argument(
            "--quiet",
            action="store_true",
            help="Quiet mode, reduce output"
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=15,
            help="Hook execution timeout in seconds (default: 15)"
        )
        parser.add_argument(
            "--version",
            action="version",
            version=f"%(prog)s {self.VERSION}"
        )
        return parser

    def is_quiet(self):
        """Check if quiet mode is enabled."""
        return self.parsed_args.quiet

    def is_non_interactive(self):
        """Check if non-interactive mode is enabled."""
        return self.parsed_args.non_interactive

    def print_info(self, message):
        """Print info message unless in quiet mode."""
        if not self.is_quiet():
            print(message)

    def print_banner(self) -> None:
        """Print installation banner."""
        if self.is_non_interactive():
            return

        print(r"""
     ____  _____ ____     ___   _   _  ____ _____ ___ ___  _   _
    |  _ \| ____|  _ \   / _ \ / \ | |/ ___|_   _|_ _/ _ \| \ | |
    | | | |  _| | |_) | | | | / _ \| | |  _  | |  | | | | |  \| |
    | |_| | |___|  _ <  | |_| / ___ \ | |_| | | |  | | |_| | |\  |
    |____/|_____|_| \_\  \___/_/   \_\_|\____| |_| |___\___/|_| \_|

              Claude Code Pushover Hook - Installer
        """)
        print(f"[INFO] Detected platform: {self.platform}")
        print()

    def get_target_directory(self) -> Path:
        """Get target project directory from args or user input."""
        # Check if target dir is provided via command line
        if self.parsed_args.target_dir:
            target = Path(self.parsed_args.target_dir).resolve()
            if not target.exists():
                if self.is_non_interactive():
                    print(json.dumps({
                        "status": "error",
                        "message": f"Target directory does not exist: {target}"
                    }))
                    sys.exit(1)
                response = input(f"Directory does not exist: {target}\nCreate it? (y/n): ").lower()
                if response == 'y':
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    sys.exit(1)

            # Check if writable
            test_file = target / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
            except Exception as e:
                print(json.dumps({
                    "status": "error",
                    "message": f"Cannot write to directory: {e}"
                }))
                sys.exit(1)

            self.print_info(f"[OK] Target directory: {target}")
            return target

        # Interactive mode
        if self.is_non_interactive():
            print(json.dumps({
                "status": "error",
                "message": "Target directory required in non-interactive mode. Use --target-dir"
            }))
            sys.exit(1)

        print("[Step 1/5] Target Project Directory")
        print("-" * 60)
        print("Enter the path to your Claude Code project.")
        print("This is where the .claude folder will be created.")
        print()

        while True:
            user_input = input("Target directory path: ").strip()

            # Handle path input
            if user_input.startswith('"') or user_input.startswith("'"):
                user_input = user_input[1:-1]

            target = Path(user_input).resolve()

            if not target.exists():
                response = input(f"Directory does not exist: {target}\nCreate it? (y/n): ").lower()
                if response == 'y':
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    continue

            # Check if writable
            test_file = target / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
            except Exception as e:
                print(f"[ERROR] Cannot write to directory: {e}")
                continue

            print(f"[OK] Target directory: {target}")
            return target

    def create_hook_directory(self) -> None:
        """Create the .claude/hooks/pushover-hook directory structure."""
        self.print_info("\n[Step 2/5] Creating Hook Directory")
        self.print_info("-" * 60)

        self.hook_dir = self.target_dir / ".claude" / "hooks" / "pushover-hook"
        cache_dir = self.target_dir / ".claude" / "cache"

        try:
            self.hook_dir.mkdir(parents=True, exist_ok=True)
            cache_dir.mkdir(parents=True, exist_ok=True)
            self.print_info(f"[OK] Created: {self.hook_dir}")
            self.print_info(f"[OK] Created: {cache_dir}")
        except Exception as e:
            print(json.dumps({
                "status": "error",
                "message": f"Failed to create directories: {e}"
            }))
            sys.exit(1)

    def copy_hook_files(self) -> None:
        """
        Copy hook script files to target directory and cleanup old files.

        从 hooks/ 目录复制文件到目标目录，然后清理旧版本的文件。
        """
        self.print_info("\n[Step 3/5] Copying Hook Files")
        self.print_info("-" * 60)

        # 从 hooks/ 目录复制（新的目录结构）
        source_hooks_dir = self.script_dir / "hooks"

        files_to_copy = [
            "pushover-notify.py",
            "test-pushover.py",
            "test-windows-notification.py",
            "diagnose.py",
            "README.md",
            "install-burnttoast.ps1",  # Windows 用户需要此脚本来安装 BurntToast 模块
        ]

        copied = 0
        for filename in files_to_copy:
            source = source_hooks_dir / filename
            target = self.hook_dir / filename

            if not source.exists():
                self.print_info(f"[WARN] Source file not found: {filename}")
                continue

            try:
                shutil.copy2(source, target)
                # Make scripts executable on Unix
                if self.platform != "Windows" and filename.endswith(".py"):
                    target.chmod(0o755)
                self.print_info(f"[OK] Copied: {filename}")
                copied += 1
            except Exception as e:
                print(json.dumps({
                    "status": "error",
                    "message": f"Failed to copy {filename}: {e}"
                }))
                sys.exit(1)

        if copied == 0:
            print(json.dumps({
                "status": "error",
                "message": "No files were copied!"
            }))
            sys.exit(1)

        # Cleanup old files after successful copy
        if copied > 0:
            self.cleanup_old_files()
            # 清理子目录中不再使用的文件
            self._cleanup_obsolete_hook_files(files_to_copy)

    def create_version_file(self) -> None:
        """Create VERSION file with version, install time, and git commit."""
        try:
            from datetime import datetime

            # Get git commit hash
            git_commit = "unknown"
            try:
                result = subprocess.run(
                    ['git', 'rev-parse', 'HEAD'],
                    cwd=self.script_dir,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    git_commit = result.stdout.strip()
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                pass

            # Create VERSION file content
            installed_at = datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            version_content = f"version={self.version}\ninstalled_at={installed_at}\ngit_commit={git_commit}\n"

            # Write VERSION file
            version_file = self.hook_dir / "VERSION"
            with open(version_file, 'w', encoding='utf-8') as f:
                f.write(version_content)

            self.print_info(f"[OK] Created VERSION file")
            self.print_info(f"[INFO] Version: {self.version}")
            self.print_info(f"[INFO] Installed at: {installed_at}")
            self.print_info(f"[INFO] Git commit: {git_commit}")

        except Exception as e:
            self.print_info(f"[WARN] Failed to create VERSION file: {e}")

    def backup_settings(self, settings_path: Path) -> Path:
        """
        Create a backup of existing settings.json.

        Args:
            settings_path: settings.json 文件路径

        Returns:
            备份文件路径，如果备份失败则返回 None
        """
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = settings_path.parent / f"settings.json.backup_{timestamp}"
            shutil.copy2(settings_path, backup_path)
            self.print_info(f"[OK] Backed up existing settings.json to:")
            self.print_info(f"     {backup_path.name}")
            return backup_path
        except Exception as e:
            self.print_info(f"[WARN] Failed to backup settings.json: {e}")
            return None

    def cleanup_old_files(self) -> None:
        """
        清理旧版本的文件。
        包括：
        - 旧的扁平结构 hook 文件（在 .claude/hooks/ 目录）
        - 旧的 __pycache__ 目录
        - 旧的禁用标志文件（.no-pushover, .no-windows）
        """
        old_hooks_dir = self.target_dir / ".claude" / "hooks"
        old_claude_dir = self.target_dir / ".claude"

        # 需要清理的旧文件
        old_files_to_cleanup = [
            "pushover-notify.py",
            "test-pushover.py",
            "diagnose.py",
            "README.md",
            "debug.log",
        ]

        existing_old_files = []
        for filename in old_files_to_cleanup:
            old_file = old_hooks_dir / filename
            if old_file.exists():
                existing_old_files.append(old_file)

        # 检查 __pycache__ 目录
        old_pycache = old_hooks_dir / "__pycache__"
        if old_pycache.exists() and old_pycache.is_dir():
            existing_old_files.append(old_pycache)

        # 检查旧的禁用标志文件
        old_disable_files = [
            old_claude_dir / ".no-pushover",
            old_claude_dir / ".no-windows",
        ]
        for disable_file in old_disable_files:
            if disable_file.exists():
                existing_old_files.append(disable_file)

        # 执行清理
        if existing_old_files:
            self.print_info(f"\n[INFO] Cleaning up {len(existing_old_files)} old file(s)...")
            for old_file in existing_old_files:
                try:
                    if old_file.is_dir():
                        shutil.rmtree(old_file)
                    else:
                        old_file.unlink()
                    self.print_info(f"[OK] Removed: {old_file.name}")
                except Exception as e:
                    self.print_info(f"[WARN] Failed to remove {old_file.name}: {e}")
                    self.print_info(f"[INFO] Please manually remove: {old_file}")
        else:
            self.print_info("\n[INFO] No old files found (fresh install or already cleaned)")

    def _cleanup_obsolete_hook_files(self, expected_files: list) -> None:
        """
        清理 pushover-hook 子目录中不再使用的文件。

        Args:
            expected_files: 期望保留的文件名列表

        逻辑：
        - 列出目标目录中的所有文件
        - 删除不在 expected_files 列表中的文件（VERSION 文件除外）
        """
        if not self.hook_dir or not self.hook_dir.exists():
            return

        # 构建期望文件集合（包括 VERSION 文件）
        expected_set = set(expected_files)
        expected_set.add("VERSION")

        # 获取实际存在的文件列表
        actual_files = []
        try:
            actual_files = [f.name for f in self.hook_dir.iterdir() if f.is_file()]
        except Exception as e:
            self.print_info(f"[WARN] Failed to list hook directory: {e}")
            return

        # 找出需要删除的过时文件
        obsolete_files = set(actual_files) - expected_set

        if obsolete_files:
            self.print_info(f"\n[INFO] Cleaning up {len(obsolete_files)} obsolete file(s) in subdirectory...")
            for filename in obsolete_files:
                file_path = self.hook_dir / filename
                try:
                    file_path.unlink()
                    self.print_info(f"[OK] Removed obsolete file: {filename}")
                except Exception as e:
                    self.print_info(f"[WARN] Failed to remove {filename}: {e}")
        else:
            self.print_info("\n[INFO] No obsolete files in subdirectory (all files up to date)")

    def merge_hook_configs(self, existing_hooks: dict, new_hooks: dict) -> dict:
        """
        Merge new hook configurations into existing ones.

        Args:
            existing_hooks: 现有的 hooks 配置
            new_hooks: 要合并的新 hooks 配置

        Returns:
            合并后的 hooks 配置字典

        Logic:
            1. 如果事件名不存在，直接添加
            2. 如果新配置包含 pushover hook，先移除旧的 pushover hook，再添加新的
            3. 如果新配置不包含 pushover hook，检查是否已存在，避免重复
        """
        merged = existing_hooks.copy()

        for event_name, event_configs in new_hooks.items():
            if event_name not in merged:
                # 事件不存在，直接添加
                merged[event_name] = event_configs
                self.print_info(f"[INFO] Added new event hooks: {event_name}")
            else:
                # 事件已存在，需要合并
                for new_event_config in event_configs:
                    new_hooks_list = new_event_config.get("hooks", [])
                    new_has_pushover = any(
                        "pushover-notify.py" in hook.get("command", "")
                        for hook in new_hooks_list
                    )

                    if new_has_pushover:
                        # 移除旧的 pushover hook
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
                            self.print_info(f"[INFO] Replaced {removed_count} old pushover hook(s) for {event_name}")

                        # 添加新的 pushover hook
                        merged[event_name].append(new_event_config)
                    else:
                        # 非_pushover hook，检查重复
                        found = False
                        for existing_event_config in merged[event_name]:
                            if existing_event_config.get("hooks") == new_event_config.get("hooks"):
                                found = True
                                break

                        if not found:
                            merged[event_name].append(new_event_config)
                            self.print_info(f"[INFO] Added new hook for {event_name}")
                        else:
                            self.print_info(f"[INFO] Hook already exists for {event_name}, skipping")

        return merged

    def get_pushover_hooks_config(self) -> dict:
        """
        获取 Pushover hooks 配置。

        使用 CLAUDE_PROJECT_DIR 环境变量实现可移植的路径配置。

        Returns:
            Pushover hooks 配置字典
        """
        # 使用环境变量 CLAUDE_PROJECT_DIR 来实现可移植的路径配置
        if self.platform == "Windows":
            # Windows 上优先使用 py 命令，更可靠
            env_check = self.check_environment()
            python_cmd = env_check.get("python_command", "py")
            command = f'set PYTHONIOENCODING=utf-8&& {python_cmd} "%CLAUDE_PROJECT_DIR%\\.claude\\hooks\\pushover-hook\\pushover-notify.py"'
        else:
            command = 'PYTHONIOENCODING=utf-8 python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/pushover-hook/pushover-notify.py"'

        return {
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

    def fresh_install(self) -> None:
        """
        全新安装模式。
        创建全新的 settings.json 文件。
        """
        self.print_info("[INFO] Installation mode: Fresh install")
        settings = {"hooks": self.get_pushover_hooks_config()}
        settings_path = self.target_dir / ".claude" / "settings.json"

        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            self.print_info(f"[OK] Created: {settings_path}")
            self.print_info(f"[INFO] Platform: {self.platform}")
        except Exception as e:
            print(json.dumps({
                "status": "error",
                "message": f"Failed to create settings.json: {e}"
            }))
            sys.exit(1)

    def migrate_from_old_version(self) -> None:
        """
        从旧版本迁移模式。
        备份现有配置，从扁平结构迁移到子目录结构。
        """
        self.print_info("[INFO] Installation mode: Migrate from old version")
        settings_path = self.target_dir / ".claude" / "settings.json"

        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                existing_settings = json.load(f)

            self.backup_settings(settings_path)

            existing_hooks = existing_settings.get("hooks", {})
            new_hooks = self.get_pushover_hooks_config()
            merged_hooks = self.merge_hook_configs(existing_hooks, new_hooks)

            existing_settings["hooks"] = merged_hooks

            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(existing_settings, f, indent=2, ensure_ascii=False)

            self.print_info(f"[OK] Migrated and merged hooks into settings.json")
            self.print_info(f"[INFO] Platform: {self.platform}")

        except json.JSONDecodeError as e:
            print(json.dumps({
                "status": "error",
                "message": f"Existing settings.json is invalid: {e}"
            }))
            sys.exit(1)
        except Exception as e:
            print(json.dumps({
                "status": "error",
                "message": f"Failed to migrate settings.json: {e}"
            }))
            sys.exit(1)

    def backup_and_upgrade(self) -> None:
        """
        备份并升级模式。
        已有新版本结构，需要升级配置。
        """
        self.print_info("[INFO] Installation mode: Backup and upgrade")
        settings_path = self.target_dir / ".claude" / "settings.json"

        if settings_path.exists():
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    existing_settings = json.load(f)

                self.backup_settings(settings_path)

                existing_hooks = existing_settings.get("hooks", {})
                new_hooks = self.get_pushover_hooks_config()
                merged_hooks = self.merge_hook_configs(existing_hooks, new_hooks)

                existing_settings["hooks"] = merged_hooks

                with open(settings_path, 'w', encoding='utf-8') as f:
                    json.dump(existing_settings, f, indent=2, ensure_ascii=False)

                self.print_info(f"[OK] Upgraded hooks in settings.json")
                self.print_info(f"[INFO] Platform: {self.platform}")

            except json.JSONDecodeError as e:
                print(json.dumps({
                    "status": "error",
                    "message": f"Existing settings.json is invalid: {e}"
                }))
                sys.exit(1)
            except Exception as e:
                print(json.dumps({
                    "status": "error",
                    "message": f"Failed to upgrade settings.json: {e}"
                }))
                sys.exit(1)
        else:
            # 没有 settings.json，创建新的
            self.fresh_install()

    def merge_to_existing_settings(self) -> None:
        """
        合并到现有配置模式。
        仅有 settings.json，需要添加 Pushover hooks。
        """
        self.print_info("[INFO] Installation mode: Merge to existing settings")
        settings_path = self.target_dir / ".claude" / "settings.json"

        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                existing_settings = json.load(f)

            self.backup_settings(settings_path)

            existing_hooks = existing_settings.get("hooks", {})
            new_hooks = self.get_pushover_hooks_config()
            merged_hooks = self.merge_hook_configs(existing_hooks, new_hooks)

            existing_settings["hooks"] = merged_hooks

            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(existing_settings, f, indent=2, ensure_ascii=False)

            self.print_info(f"[OK] Merged Pushover hooks into existing settings.json")
            self.print_info(f"[INFO] Platform: {self.platform}")

        except json.JSONDecodeError as e:
            print(json.dumps({
                "status": "error",
                "message": f"Existing settings.json is invalid: {e}"
            }))
            sys.exit(1)
        except Exception as e:
            print(json.dumps({
                "status": "error",
                "message": f"Failed to merge settings.json: {e}"
            }))
            sys.exit(1)

    def merge_settings_and_generate(self) -> None:
        """
        仅合并配置模式。
        Hook 文件已存在，只需更新配置。
        """
        self.print_info("[INFO] Installation mode: Merge settings only")
        settings_path = self.target_dir / ".claude" / "settings.json"

        if settings_path.exists():
            self.merge_to_existing_settings()
        else:
            self.fresh_install()

    def check_environment(self) -> dict:
        """
        检查系统环境依赖项。

        Returns:
            包含环境检查结果的字典:
            - python_available: bool - Python 是否可用
            - python_command: str - 可用的 Python 命令 (python/python3/py)
            - burnttoast_available: bool - Windows 上 BurntToast 模块是否可用
            - pushover_configured: bool - Pushover 环境变量是否已配置
            - has_token: bool - PUSHOVER_TOKEN 是否设置
            - has_user: bool - PUSHOVER_USER 是否设置
        """
        env_status = {
            "python_available": False,
            "python_command": None,
            "burnttoast_available": False,
            "pushover_configured": False,
            "has_token": False,
            "has_user": False
        }

        # 检查 Python
        if self.platform == "Windows":
            # Windows: 优先尝试 py launcher
            for cmd in ["py", "python"]:
                try:
                    result = subprocess.run(
                        [cmd, "--version"],
                        capture_output=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        env_status["python_available"] = True
                        env_status["python_command"] = cmd
                        break
                except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                    continue
        else:
            # Linux/Mac: 尝试 python3 或 python
            for cmd in ["python3", "python"]:
                try:
                    result = subprocess.run(
                        [cmd, "--version"],
                        capture_output=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        env_status["python_available"] = True
                        env_status["python_command"] = cmd
                        break
                except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                    continue

        # 检查 BurntToast (仅 Windows)
        if self.platform == "Windows" and env_status["python_available"]:
            env_status["burnttoast_available"] = self._check_burnttoast(env_status["python_command"])

        # 检查 Pushover 环境变量
        env_status["has_token"] = bool(os.environ.get("PUSHOVER_TOKEN"))
        env_status["has_user"] = bool(os.environ.get("PUSHOVER_USER"))
        env_status["pushover_configured"] = env_status["has_token"] and env_status["has_user"]

        return env_status

    def _check_burnttoast(self, python_cmd: str) -> bool:
        """
        检查 BurntToast PowerShell 模块是否可用。

        Args:
            python_cmd: 可用的 Python 命令

        Returns:
            bool - BurntToast 是否可用
        """
        try:
            # 使用 PowerShell 检查模块
            result = subprocess.run(
                ["powershell", "-Command", "Get-Module -ListAvailable -Name BurntToast"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False

    def show_environment_status(self, env_status: dict) -> None:
        """
        显示环境状态信息。

        Args:
            env_status: check_environment() 返回的状态字典
        """
        if self.is_non_interactive():
            self._show_environment_json(env_status)
        else:
            self._show_environment_interactive(env_status)

    def _show_environment_interactive(self, env_status: dict) -> None:
        """在交互模式下显示环境状态。"""
        print("\n" + "=" * 60)
        print("Environment Status")
        print("=" * 60)
        print()

        # Python 状态
        python_status = "[OK]" if env_status["python_available"] else "[FAIL]"
        python_cmd = env_status.get("python_command", "Not found")
        print(f"Python:     {python_status}  ({python_cmd})")

        # Pushover 状态
        token_status = "[OK]" if env_status["has_token"] else "[MISSING]"
        user_status = "[OK]" if env_status["has_user"] else "[MISSING]"
        print(f"PUSHOVER_TOKEN:  {token_status}")
        print(f"PUSHOVER_USER:   {user_status}")

        # Windows 特定状态
        if self.platform == "Windows":
            bt_status = "[OK]" if env_status["burnttoast_available"] else "[NOT INSTALLED]"
            print(f"BurntToast:  {bt_status}  (Windows notifications)")

        print()
        print("=" * 60)

        # 显示指南
        if not env_status["pushover_configured"]:
            print("\n[INFO] Pushover environment variables not configured")
            print("Please set the following environment variables:")
            print("  - PUSHOVER_TOKEN (get from https://pushover.net/apps)")
            print("  - PUSHOVER_USER  (get from https://pushover.net/)")
            print()

        if self.platform == "Windows" and not env_status["burnttoast_available"]:
            print("[INFO] BurntToast module not installed")
            print("Windows desktop notifications will not be available")
            print("To install, run (as Administrator):")
            print("  Install-Module -Name BurntToast -Force")
            print()

        if self.platform == "Windows" and not env_status["python_available"]:
            self._show_windows_dependency_guide()

    def _show_environment_json(self, env_status: dict) -> None:
        """在非交互模式下以 JSON 格式显示环境状态。"""
        output = {
            "status": "success",
            "environment": env_status
        }
        print(json.dumps(output, indent=2))

    def _show_windows_dependency_guide(self) -> None:
        """显示 Windows 依赖项安装指南。"""
        print()
        print("=" * 60)
        print("Windows Dependencies Installation Guide")
        print("=" * 60)
        print()
        print("Python is not installed or not found on your system.")
        print()
        print("To install Python:")
        print("  1. Visit: https://www.python.org/downloads/")
        print("  2. Download and run the installer")
        print("  3. IMPORTANT: Check 'Add Python to PATH' during installation")
        print()
        print("After installation, restart your terminal and run this script again.")
        print()
        print("Alternatively, install Python using the Microsoft Store:")
        print("  - Search 'Python' in Microsoft Store")
        print("  - Install the latest version (3.10 or later recommended)")
        print()
        print("=" * 60)

    def generate_settings_json(self) -> None:
        """Generate or merge platform-specific settings.json."""
        self.print_info("\n[Step 4/5] Generating Configuration")
        self.print_info("-" * 60)

        # 使用环境变量 CLAUDE_PROJECT_DIR 来实现可移植的路径配置
        if self.platform == "Windows":
            # Windows 上优先使用 py 命令，更可靠
            env_check = self.check_environment()
            python_cmd = env_check.get("python_command", "py")
            command = f'set PYTHONIOENCODING=utf-8&& {python_cmd} "%CLAUDE_PROJECT_DIR%\\.claude\\hooks\\pushover-hook\\pushover-notify.py"'
        else:
            command = 'PYTHONIOENCODING=utf-8 python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/pushover-hook/pushover-notify.py"'

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

        settings_path = self.target_dir / ".claude" / "settings.json"

        if settings_path.exists():
            self.print_info(f"[INFO] Existing settings.json found")
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    existing_settings = json.load(f)

                self.backup_settings(settings_path)

                existing_hooks = existing_settings.get("hooks", {})
                merged_hooks = self.merge_hook_configs(existing_hooks, pushover_hooks)

                existing_settings["hooks"] = merged_hooks

                with open(settings_path, 'w', encoding='utf-8') as f:
                    json.dump(existing_settings, f, indent=2, ensure_ascii=False)

                self.print_info(f"[OK] Merged Pushover hooks into existing settings.json")
                self.print_info(f"[INFO] Platform: {self.platform}")
                self.print_info(f"[INFO] Command uses CLAUDE_PROJECT_DIR for portability")

            except json.JSONDecodeError as e:
                print(json.dumps({
                    "status": "error",
                    "message": f"Existing settings.json is invalid: {e}"
                }))
                sys.exit(1)
            except Exception as e:
                print(json.dumps({
                    "status": "error",
                    "message": f"Failed to merge settings.json: {e}"
                }))
                sys.exit(1)
        else:
            settings = {"hooks": pushover_hooks}
            try:
                with open(settings_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=2, ensure_ascii=False)
                self.print_info(f"[OK] Created: {settings_path}")
                self.print_info(f"[INFO] Platform: {self.platform}")
                self.print_info(f"[INFO] Command uses CLAUDE_PROJECT_DIR for portability")
            except Exception as e:
                print(json.dumps({
                    "status": "error",
                    "message": f"Failed to create settings.json: {e}"
                }))
                sys.exit(1)

    def show_env_instructions(self) -> None:
        """Show environment variable setup instructions."""
        if self.is_non_interactive():
            return

        self.print_info("\n[Step 5/5] Environment Variables")
        self.print_info("-" * 60)
        self.print_info("You need to set the following environment variables:")
        print()
        self.print_info("  PUSHOVER_TOKEN  - Your Pushover application token")
        self.print_info("  PUSHOVER_USER   - Your Pushover user key")
        print()
        self.print_info("Get them from:")
        self.print_info("  - Token: https://pushover.net/apps")
        self.print_info("  - User:  https://pushover.net/")
        print()
        self.print_info("Set them using:")
        print()

        if self.platform == "Windows":
            self.print_info("  # Command Prompt (temporary)")
            self.print_info("  set PUSHOVER_TOKEN=your_token_here")
            self.print_info("  set PUSHOVER_USER=your_user_key_here")
            print()
            self.print_info("  # PowerShell (temporary)")
            self.print_info("  $env:PUSHOVER_TOKEN=\"your_token_here\"")
            self.print_info("  $env:PUSHOVER_USER=\"your_user_key_here\"")
        else:
            shell = os.environ.get("SHELL", "bash")
            rc_file = "~/.zshrc" if "zsh" in shell else "~/.bashrc"
            self.print_info(f"  # Temporary (current session only)")
            self.print_info("  export PUSHOVER_TOKEN=your_token_here")
            self.print_info("  export PUSHOVER_USER=your_user_key_here")
            print()
            self.print_info(f"  # Permanent (add to {rc_file})")

    def print_completion_message(self, action: str) -> None:
        """
        打印安装完成消息。

        Args:
            action: 执行的安装动作类型
        """
        if self.is_non_interactive():
            return

        print("\n" + "=" * 60)
        print("Installation Complete!")
        print("=" * 60)
        print()
        print(f"Action performed: {action}")
        print(f"Version: {self.version}")
        print()

        print("Next steps:")
        print()
        print("1. Check environment status")
        print("2. Set environment variables if needed (shown above)")
        print("3. Run the diagnostic script:")
        print()

        if self.platform == "Windows":
            print(f"   py {self.hook_dir}\\diagnose.py")
        else:
            print(f"   python3 {self.hook_dir}/diagnose.py")

        print()
        print("4. Send a test notification:")
        print()

        if self.platform == "Windows":
            print(f"   py {self.hook_dir}\\test-pushover.py")
        else:
            print(f"   python3 {self.hook_dir}/test-pushover.py")

        print()
        print("5. Trigger a Claude Code task and check for notifications!")
        print()

    def handle_error(self, error: Exception) -> None:
        """
        统一错误处理。

        Args:
            error: 捕获的异常对象
        """
        if self.is_non_interactive():
            print(json.dumps({
                "status": "error",
                "message": str(error)
            }))
        else:
            print(f"\n[ERROR] Installation failed: {error}")
            import traceback
            traceback.print_exc()
        sys.exit(1)

    def run_installation_action(self, action: str) -> None:
        """
        根据安装动作类型执行相应的安装流程。

        Args:
            action: 安装动作类型
        """
        # 步骤 1-3: 准备工作（所有动作都需要）
        self.create_hook_directory()
        self.copy_hook_files()
        self.create_version_file()

        # 步骤 4: 配置生成（根据动作类型）
        self.print_info("\n[Step 4/5] Generating Configuration")
        self.print_info("-" * 60)

        if action == 'fresh_install':
            self.fresh_install()
        elif action == 'migrate_from_old':
            self.migrate_from_old_version()
        elif action == 'backup_and_upgrade':
            self.backup_and_upgrade()
        elif action == 'merge_to_existing':
            self.merge_to_existing_settings()
        elif action == 'merge_settings_only':
            self.merge_settings_and_generate()
        else:
            # 未知动作，回退到默认行为
            self.print_info(f"[WARN] Unknown action '{action}', using default installation")
            self.fresh_install()

    def run_verification(self, action: str) -> None:
        """
        运行安装后验证和诊断。

        Args:
            action: 执行的安装动作类型
        """
        if self.parsed_args.skip_diagnostics:
            return

        if self.is_non_interactive():
            return

        # 显示环境状态
        env_status = self.check_environment()
        self.show_environment_status(env_status)

        # 显示环境变量说明
        self.show_env_instructions()

        # 打印完成消息
        self.print_completion_message(action)

        # 询问是否运行诊断
        response = input("\nRun diagnostics now? (y/n): ").lower()
        if response == 'y':
            diagnose_script = self.hook_dir / "diagnose.py"
            if diagnose_script.exists():
                print("\n" + "-" * 60)
                print("Running diagnostics...")
                print("-" * 60)
                import subprocess
                result = subprocess.run(
                    [sys.executable, str(diagnose_script)],
                    cwd=str(self.target_dir),
                    env=os.environ.copy()
                )
                print()
                if result.returncode == 0:
                    print("[INFO] Diagnostics completed.")
                else:
                    print("[WARN] Diagnostics reported issues. Please fix them above.")

    def run(self) -> None:
        """
        Run the full installation process.

        重构后的主运行流程:
        1. 显示横幅
        2. 获取目标目录
        3. 检测现有安装
        4. 确定安装动作
        5. 执行安装动作
        6. 运行验证
        7. 输出结果
        """
        try:
            # 步骤 1: 显示横幅
            self.print_banner()

            # 步骤 2: 获取目标目录
            self.target_dir = self.get_target_directory()

            # 步骤 3: 检测现有安装状态
            self.print_info("[INFO] Detecting existing installation...")
            detection = self.detect_existing_installation()

            # 步骤 4: 确定安装动作
            action = self.determine_install_action(detection)
            self.print_info(f"[INFO] Installation action: {action}")

            # 步骤 5: 执行安装动作
            self.run_installation_action(action)

            # 步骤 6: 运行验证
            self.run_verification(action)

            # 步骤 7: 输出 JSON 结果（非交互模式）
            if self.is_non_interactive():
                result = {
                    "status": "success",
                    "action": action,
                    "hook_path": str(self.hook_dir),
                    "version": self.version
                }
                print(json.dumps(result))

        except KeyboardInterrupt:
            if self.is_non_interactive():
                print(json.dumps({"status": "cancelled", "message": "Installation cancelled"}))
            else:
                print("\n\n[INFO] Installation cancelled by user.")
            sys.exit(0)
        except Exception as e:
            self.handle_error(e)


def main() -> None:
    """Main entry point."""
    installer = Installer(sys.argv[1:])
    installer.run()


if __name__ == "__main__":
    main()
