#!/usr/bin/env python3
"""
Cross-platform installer for Claude Code Pushover notification hook.

Usage:
    python install.py [OPTIONS]

Options:
    -t, --target-dir PATH    Target project directory (required for non-interactive mode)
    --force                  Force reinstall, overwrite existing files
    --non-interactive        Non-interactive mode, don't ask for confirmation
    --skip-diagnostics       Skip post-install diagnostics
    --quiet                  Quiet mode, reduce output
    --version                Show version information

The script will:
1. Detect your platform (Windows/Linux/macOS)
2. Ask for the target project directory (or use --target-dir)
3. Copy all necessary files
4. Generate platform-specific settings.json
5. Guide you through environment variable setup
6. Run diagnostics to verify installation (unless --skip-diagnostics)
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

        # Debug: print received args
        import sys
        print(f"[DEBUG] sys.argv: {sys.argv}", file=sys.stderr)
        print(f"[DEBUG] args parameter: {args}", file=sys.stderr)

        # Debug: print parsed args
        print(f"[DEBUG] parsed_args.target_dir: {self.parsed_args.target_dir}", file=sys.stderr)
        print(f"[DEBUG] parsed_args.non_interactive: {self.parsed_args.non_interactive}", file=sys.stderr)

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
        """Copy hook script files to target directory and cleanup old files."""
        self.print_info("\n[Step 3/5] Copying Hook Files")
        self.print_info("-" * 60)

        # Detect old files from previous installation
        old_hooks_dir = self.target_dir / ".claude" / "hooks"
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

        # Check for __pycache__ directory
        old_pycache = old_hooks_dir / "__pycache__"
        if old_pycache.exists() and old_pycache.is_dir():
            existing_old_files.append(old_pycache)

        # Check for old disable flag files in .claude directory
        old_claude_dir = self.target_dir / ".claude"
        old_disable_files = [
            old_claude_dir / ".no-pushover",
            old_claude_dir / ".no-windows",
        ]
        for disable_file in old_disable_files:
            if disable_file.exists():
                existing_old_files.append(disable_file)

        source_hooks_dir = self.script_dir / ".claude" / "hooks" / "pushover-hook"

        files_to_copy = [
            "pushover-notify.py",
            "test-pushover.py",
            "test-windows-notification.py",
            "diagnose.py",
            "README.md",
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
        if copied > 0 and existing_old_files:
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
        elif copied > 0:
            self.print_info("\n[INFO] No old files found (fresh install or already cleaned)")

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
            installed_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
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

    def backup_settings(self, settings_path: Path) -> None:
        """Create a backup of existing settings.json."""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = settings_path.parent / f"settings.json.backup_{timestamp}"
            shutil.copy2(settings_path, backup_path)
            self.print_info(f"[OK] Backed up existing settings.json to:")
            self.print_info(f"     {backup_path.name}")
        except Exception as e:
            self.print_info(f"[WARN] Failed to backup settings.json: {e}")

    def merge_hook_configs(self, existing_hooks: dict, new_hooks: dict) -> dict:
        """
        Merge new hook configurations into existing ones.
        """
        merged = existing_hooks.copy()

        for event_name, event_configs in new_hooks.items():
            if event_name not in merged:
                merged[event_name] = event_configs
            else:
                for new_event_config in event_configs:
                    new_hooks_list = new_event_config.get("hooks", [])
                    new_has_pushover = any(
                        "pushover-notify.py" in hook.get("command", "")
                        for hook in new_hooks_list
                    )

                    if new_has_pushover:
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

                        merged[event_name].append(new_event_config)
                    else:
                        found = False
                        for existing_event_config in merged[event_name]:
                            if existing_event_config.get("hooks") == new_event_config.get("hooks"):
                                found = True
                                break

                        if not found:
                            merged[event_name].append(new_event_config)
                        else:
                            self.print_info(f"[INFO] Hook already exists for {event_name}, skipping")

        return merged

    def generate_settings_json(self) -> None:
        """Generate or merge platform-specific settings.json."""
        self.print_info("\n[Step 4/5] Generating Configuration")
        self.print_info("-" * 60)

        hook_script_path = self.hook_dir / "pushover-notify.py"

        if self.platform == "Windows":
            command = f"set PYTHONIOENCODING=utf-8&& python \"{hook_script_path}\""
        else:
            command = f"PYTHONIOENCODING=utf-8 \"{hook_script_path}\""

        pushover_hooks = {
            "UserPromptSubmit": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": command
                        }
                    ]
                }
            ],
            "Stop": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": command
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
                            "command": command
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
                self.print_info(f"[INFO] Command: {command}")

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
                self.print_info(f"[INFO] Command: {command}")
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
        self.print_info()
        self.print_info("  PUSHOVER_TOKEN  - Your Pushover application token")
        self.print_info("  PUSHOVER_USER   - Your Pushover user key")
        self.print_info()
        self.print_info("Get them from:")
        self.print_info("  - Token: https://pushover.net/apps")
        self.print_info("  - User:  https://pushover.net/")
        self.print_info()
        self.print_info("Set them using:")
        self.print_info()

        if self.platform == "Windows":
            self.print_info("  # Command Prompt (temporary)")
            self.print_info("  set PUSHOVER_TOKEN=your_token_here")
            self.print_info("  set PUSHOVER_USER=your_user_key_here")
            self.print_info()
            self.print_info("  # PowerShell (temporary)")
            self.print_info("  $env:PUSHOVER_TOKEN=\"your_token_here\"")
            self.print_info("  $env:PUSHOVER_USER=\"your_user_key_here\"")
        else:
            shell = os.environ.get("SHELL", "bash")
            rc_file = "~/.zshrc" if "zsh" in shell else "~/.bashrc"
            self.print_info(f"  # Temporary (current session only)")
            self.print_info("  export PUSHOVER_TOKEN=your_token_here")
            self.print_info("  export PUSHOVER_USER=your_user_key_here")
            self.print_info()
            self.print_info(f"  # Permanent (add to {rc_file})")

    def run_verification(self) -> None:
        """Run diagnostic script to verify installation."""
        if self.parsed_args.skip_diagnostics:
            return

        if self.is_non_interactive():
            return

        print("\n" + "=" * 60)
        print("Installation Complete!")
        print("=" * 60)
        print()
        print("Next steps:")
        print()
        print("1. Set the environment variables (shown above)")
        print("2. Run the diagnostic script:")
        print()

        if self.platform == "Windows":
            print(f"   python {self.hook_dir}\\diagnose.py")
        else:
            print(f"   python {self.hook_dir}/diagnose.py")

        print()
        print("3. Send a test notification:")
        print()

        if self.platform == "Windows":
            print(f"   python {self.hook_dir}\\test-pushover.py")
        else:
            print(f"   python {self.hook_dir}/test-pushover.py")

        print()
        print("4. Trigger a Claude Code task and check for notifications!")
        print()

        response = input("Run diagnostics now? (y/n): ").lower()
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
        """Run the full installation process."""
        try:
            self.print_banner()
            self.target_dir = self.get_target_directory()
            self.create_hook_directory()
            self.copy_hook_files()
            self.create_version_file()
            self.generate_settings_json()
            self.show_env_instructions()
            self.run_verification()

            # Output JSON result in non-interactive mode
            if self.is_non_interactive():
                result = {
                    "status": "success",
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
            if self.is_non_interactive():
                print(json.dumps({
                    "status": "error",
                    "message": str(e)
                }))
            else:
                print(f"\n[ERROR] Installation failed: {e}")
                import traceback
                traceback.print_exc()
            sys.exit(1)


def main() -> None:
    """Main entry point."""
    installer = Installer(sys.argv[1:])
    installer.run()


if __name__ == "__main__":
    main()
