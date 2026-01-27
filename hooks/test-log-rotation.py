#!/usr/bin/env python3
"""
Test helper for log rotation functionality.
Creates test log files with various dates and verifies cleanup.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import re
import argparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import cleanup_old_logs from pushover-notify.py (with hyphens)
import importlib.util
spec = importlib.util.spec_from_file_location("pushover_notify", Path(__file__).parent / "pushover-notify.py")
pushover_notify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pushover_notify)
cleanup_old_logs = pushover_notify.cleanup_old_logs


def create_test_logs(log_dir: Path) -> list:
    """Create test log files with various dates."""
    today = datetime.now()
    test_files = []

    # Current log (should never be deleted)
    current = log_dir / "debug.log"
    current.touch()
    test_files.append(("debug.log", "current log"))

    # Recent logs (should be kept)
    for i in range(3):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        log_file = log_dir / f"debug.{date}.log"
        log_file.touch()
        test_files.append((log_file.name, f"{i} days old - should keep"))

    # Old logs (should be deleted)
    for i in range(4, 10):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        log_file = log_dir / f"debug.{date}.log"
        log_file.touch()
        test_files.append((log_file.name, f"{i} days old - should delete"))

    # Invalid format (should be ignored/skipped)
    invalid = log_dir / "debug.invalid.log"
    invalid.touch()
    test_files.append((invalid.name, "invalid format - should be ignored"))

    print("Created test log files:")
    for name, desc in test_files:
        print(f"  {name}: {desc}")
    return test_files


def main():
    """Run test."""
    parser = argparse.ArgumentParser(description="Test log rotation")
    parser.add_argument("--cleanup", action="store_true", help="Run cleanup after creating test files")
    args = parser.parse_args()

    # Use script directory as log dir for testing
    log_dir = Path(__file__).parent

    print(f"Test directory: {log_dir}")
    print()

    # Create test logs
    create_test_logs(log_dir)
    print()

    if args.cleanup:
        print("Running cleanup_old_logs()...")
        cleanup_old_logs(log_dir)
        print()

        # Check remaining files
        print("Remaining log files after cleanup:")
        for log_file in sorted(log_dir.glob("debug*.log")):
            print(f"  {log_file.name}")

        # Verify expected files remain
        remaining = [f.name for f in log_dir.glob("debug*.log")]

        print()
        print("Verification:")
        if "debug.log" in remaining:
            print("  [OK] debug.log preserved")
        else:
            print("  [FAIL] debug.log was deleted!")

        recent_count = sum(1 for f in remaining if re.match(r"debug\.\d{4}-\d{2}-\d{2}\.log", f))
        print(f"  [INFO] {recent_count} dated log file(s) remaining")

        if "debug.invalid.log" in remaining:
            print("  [OK] Invalid format file ignored (not deleted)")

        # Cleanup test files
        print()
        response = input("Clean up test files? (y/n): ")
        if response.lower() == 'y':
            for f in log_dir.glob("debug*.log"):
                if f.name.startswith("debug."):
                    f.unlink()
            print("Test files cleaned up.")

    else:
        print("Test files created. Run with --cleanup to test cleanup function.")


if __name__ == "__main__":
    main()
