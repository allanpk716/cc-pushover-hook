#!/usr/bin/env python3
"""
Cross-platform installer for Claude Code Pushover notification hook.

Usage:
    python install.py

The script will:
1. Detect your platform (Windows/Linux/macOS)
2. Ask for the target project directory
3. Copy all necessary files
4. Generate platform-specific settings.json
5. Guide you through environment variable setup
6. Run diagnostics to verify installation
"""

import os
import shutil
import sys
import json
from pathlib import Path
from platform import system


class Installer:
    """Cross-platform installer for Pushover hook."""

    def __init__(self):
        self.platform = system()
        self.script_dir = Path(__file__).parent.resolve()
        self.target_dir = None
        self.hook_dir = None

    def print_banner(self) -> None:
        """Print installation banner."""
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
        """Ask user for target project directory."""
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
        """Create the .claude/hooks directory structure."""
        print("\n[Step 2/5] Creating Hook Directory")
        print("-" * 60)

        self.hook_dir = self.target_dir / ".claude" / "hooks"
        cache_dir = self.target_dir / ".claude" / "cache"

        try:
            self.hook_dir.mkdir(parents=True, exist_ok=True)
            cache_dir.mkdir(parents=True, exist_ok=True)
            print(f"[OK] Created: {self.hook_dir}")
            print(f"[OK] Created: {cache_dir}")
        except Exception as e:
            print(f"[ERROR] Failed to create directories: {e}")
            sys.exit(1)

    def copy_hook_files(self) -> None:
        """Copy hook script files to target directory."""
        print("\n[Step 3/5] Copying Hook Files")
        print("-" * 60)

        source_hooks_dir = self.script_dir / ".claude" / "hooks"

        files_to_copy = [
            "pushover-notify.py",
            "test-pushover.py",
            "diagnose.py",
            "README.md",
        ]

        copied = 0
        for filename in files_to_copy:
            source = source_hooks_dir / filename
            target = self.hook_dir / filename

            if not source.exists():
                print(f"[WARN] Source file not found: {filename}")
                continue

            try:
                shutil.copy2(source, target)
                # Make scripts executable on Unix
                if self.platform != "Windows" and filename.endswith(".py"):
                    target.chmod(0o755)
                print(f"[OK] Copied: {filename}")
                copied += 1
            except Exception as e:
                print(f"[ERROR] Failed to copy {filename}: {e}")

        if copied == 0:
            print("[ERROR] No files were copied!")
            sys.exit(1)

    def generate_settings_json(self) -> None:
        """Generate platform-specific settings.json."""
        print("\n[Step 4/5] Generating Configuration")
        print("-" * 60)

        # Determine the command format based on platform
        if self.platform == "Windows":
            # Windows: need to use python command
            # The $CLAUDE_PROJECT_DIR variable expansion handles paths with spaces
            # Don't add extra quotes around the variable reference
            command = 'python "$CLAUDE_PROJECT_DIR\\.claude\\hooks\\pushover-notify.py"'
        else:
            # Unix: can use shebang
            command = '"$CLAUDE_PROJECT_DIR/.claude/hooks/pushover-notify.py"'

        settings = {
            "hooks": {
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
        }

        settings_path = self.target_dir / ".claude" / "settings.json"
        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            print(f"[OK] Created: {settings_path}")
            print(f"[INFO] Platform: {self.platform}")
            print(f"[INFO] Command: {command}")
        except Exception as e:
            print(f"[ERROR] Failed to create settings.json: {e}")
            sys.exit(1)

    def show_env_instructions(self) -> None:
        """Show environment variable setup instructions."""
        print("\n[Step 5/5] Environment Variables")
        print("-" * 60)
        print("You need to set the following environment variables:")
        print()
        print("  PUSHOVER_TOKEN  - Your Pushover application token")
        print("  PUSHOVER_USER   - Your Pushover user key")
        print()
        print("Get them from:")
        print("  - Token: https://pushover.net/apps")
        print("  - User:  https://pushover.net/")
        print()
        print("Set them using:")
        print()

        if self.platform == "Windows":
            print("  # Command Prompt (temporary)")
            print("  set PUSHOVER_TOKEN=your_token_here")
            print("  set PUSHOVER_USER=your_user_key_here")
            print()
            print("  # PowerShell (temporary)")
            print("  $env:PUSHOVER_TOKEN=\"your_token_here\"")
            print("  $env:PUSHOVER_USER=\"your_user_key_here\"")
            print()
            print("  # Permanent (System Environment Variables)")
            print("  1. Search for 'Environment Variables' in Windows")
            print("  2. Click 'Edit the system environment variables'")
            print("  3. Click 'Environment Variables'")
            print("  4. Add new variables under User variables")
        else:
            # Linux/macOS
            shell = os.environ.get("SHELL", "bash")
            if "zsh" in shell:
                rc_file = "~/.zshrc"
            else:
                rc_file = "~/.bashrc"

            print(f"  # Temporary (current session only)")
            print("  export PUSHOVER_TOKEN=your_token_here")
            print("  export PUSHOVER_USER=your_user_key_here")
            print()
            print(f"  # Permanent (add to {rc_file})")
            print("  echo 'export PUSHOVER_TOKEN=your_token_here' >> ~/.bashrc")
            print("  echo 'export PUSHOVER_USER=your_user_key_here' >> ~/.bashrc")
            print("  source ~/.bashrc")

    def run_verification(self) -> None:
        """Run diagnostic script to verify installation."""
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

        # Ask if user wants to run diagnostics now
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
        self.print_banner()

        try:
            self.target_dir = self.get_target_directory()
            self.create_hook_directory()
            self.copy_hook_files()
            self.generate_settings_json()
            self.show_env_instructions()
            self.run_verification()
        except KeyboardInterrupt:
            print("\n\n[INFO] Installation cancelled by user.")
            sys.exit(0)
        except Exception as e:
            print(f"\n[ERROR] Installation failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main() -> None:
    """Main entry point."""
    installer = Installer()
    installer.run()


if __name__ == "__main__":
    main()
