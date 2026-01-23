# Log Rotation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement automatic log rotation for debug.log, keeping maximum 3 days of logs with date-based naming.

**Architecture:** Add cleanup function triggered on script startup, scanning for debug.YYYY-MM-DD.log files and removing those older than 3 days.

**Tech Stack:** Python 3.7+, pathlib, datetime, re

---

## Task 1: Add Required Imports

**Files:**
- Modify: `.claude/hooks/pushover-hook/pushover-notify.py:10-15`

**Step 1: Read current imports section**

Run: Read lines 1-20 of pushover-notify.py to understand current imports

**Step 2: Add new imports**

Add after line 14 (`from datetime import datetime`):

```python
import re
from datetime import timedelta
```

**Step 3: Run syntax check**

Run: `python -m py_compile .claude/hooks/pushover-hook/pushover-notify.py`
Expected: No syntax errors

**Step 4: Commit**

```bash
git add .claude/hooks/pushover-hook/pushover-notify.py
git commit -m "feat(log): add imports for log rotation (re, timedelta)"
```

---

## Task 2: Implement cleanup_old_logs Function

**Files:**
- Modify: `.claude/hooks/pushover-hook/pushover-notify.py:35` (insert after log function, before is_notification_disabled)

**Step 1: Add the cleanup function**

Insert at line 36 (after `log` function, before `is_notification_disabled`):

```python
def cleanup_old_logs(log_dir: Path, keep_days: int = 3) -> None:
    """
    Clean up old log files older than keep_days.

    Only processes files matching debug.YYYY-MM-DD.log pattern.
    Never deletes the current debug.log file.

    Args:
        log_dir: Directory containing log files
        keep_days: Number of days to keep logs (default: 3)
    """
    if not log_dir.exists():
        return

    try:
        today = datetime.now().date()
        cutoff_date = today - timedelta(days=keep_days)
        log_pattern = re.compile(r'debug\.(\d{4}-\d{2}-\d{2})\.log')

        for log_file in log_dir.glob("debug*.log"):
            # Skip current debug.log
            if log_file.name == "debug.log":
                continue

            # Extract date from filename
            match = log_pattern.match(log_file.name)
            if not match:
                continue

            try:
                file_date = datetime.strptime(match.group(1), "%Y-%m-%d").date()
                if file_date < cutoff_date:
                    log_file.unlink(missing_ok=True)
                    log(f"Cleaned up old log: {log_file.name}")
            except ValueError:
                # Invalid date format, skip
                pass
            except Exception as e:
                # Log error but continue processing
                log(f"Error cleaning log file {log_file.name}: {e}")
    except Exception:
        # Silently fail - cleanup should never break the hook
        pass
```

**Step 2: Run syntax check**

Run: `python -m py_compile .claude/hooks/pushover-hook/pushover-notify.py`
Expected: No syntax errors

**Step 3: Commit**

```bash
git add .claude/hooks/pushover-hook/pushover-notify.py
git commit -m "feat(log): add cleanup_old_logs function"
```

---

## Task 3: Call cleanup_old_logs in main()

**Files:**
- Modify: `.claude/hooks/pushover-hook/pushover-notify.py:287` (after "Hook script started" log message)

**Step 1: Find exact location in main function**

Read the main function around line 287 to find the exact location after `log(f"Hook script started - Event: Processing")`

**Step 2: Add cleanup call**

After the line `log(f"Hook script started - Event: Processing")`, add:

```python
        # Clean up old log files
        cleanup_old_logs(get_log_path().parent)
```

Ensure proper indentation (4 spaces, aligned with other log calls in main).

**Step 3: Run syntax check**

Run: `python -m py_compile .claude/hooks/pushover-hook/pushover-notify.py`
Expected: No syntax errors

**Step 4: Commit**

```bash
git add .claude/hooks/pushover-hook/pushover-notify.py
git commit -m "feat(log): trigger log cleanup on script startup"
```

---

## Task 4: Create Test Helper Script

**Files:**
- Create: `.claude/hooks/pushover-hook/test-log-rotation.py`

**Step 1: Create test helper script**

```python
#!/usr/bin/env python3
"""
Test helper for log rotation functionality.
Creates test log files with various dates and verifies cleanup.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from pushover_notify import cleanup_old_logs


def create_test_logs(log_dir: Path) -> None:
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
    import argparse
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
        expected_patterns = ["debug.log", "debug.\\d{4}-\\d{2}-\\d{2}.log"]
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
    import re
    main()
```

**Step 2: Run syntax check**

Run: `python -m py_compile .claude/hooks/pushover-hook/test-log-rotation.py`
Expected: No syntax errors

**Step 3: Make executable (Unix only)**

```bash
chmod +x .claude/hooks/pushover-hook/test-log-rotation.py
```

**Step 4: Commit**

```bash
git add .claude/hooks/pushover-hook/test-log-rotation.py
git commit -m "test(log): add log rotation test helper"
```

---

## Task 5: Test Log Rotation Functionality

**Files:**
- Test: `.claude/hooks/pushover-hook/test-log-rotation.py`

**Step 1: Create test log files**

Run: `python .claude/hooks/pushover-hook/test-log-rotation.py`
Expected: Creates test log files with various dates

**Step 2: Run cleanup test**

Run: `python .claude/hooks/pushover-hook/test-log-rotation.py --cleanup`
Expected:
- Old logs (>3 days) are deleted
- Recent logs (<=3 days) are kept
- debug.log is never deleted
- Invalid format files are ignored

**Step 3: Verify output**

Check console output confirms:
- [OK] debug.log preserved
- dated log files remaining (should be 3-4 including today)
- Invalid format files ignored

**Step 4: Clean up test files**

When prompted, enter 'y' to remove test files.

**Step 5: Update README**

Update `.claude/hooks/pushover-hook/README.md` to document log rotation behavior:

```markdown
## Log Rotation

Debug logs are automatically rotated to prevent disk space issues:
- Current log: `debug.log`
- Historical logs: `debug.YYYY-MM-DD.log`
- Retention: Maximum 3 days of logs
- Cleanup: Runs automatically on script startup
```

**Step 6: Commit documentation**

```bash
git add .claude/hooks/pushover-hook/README.md
git commit -m "docs(log): document log rotation behavior"
```

---

## Task 6: Integration Test

**Files:**
- Test: Full integration test

**Step 1: Trigger actual hook**

Run any Claude Code task in a project with the hook installed.

**Step 2: Check debug.log**

Verify that a cleanup message appears in debug.log:
```
[timestamp] Cleaned up old log: debug.2025-01-15.log
```

**Step 3: Verify log files**

Check `.claude/hooks/pushover-hook/` directory:
- `debug.log` exists
- Only recent dated logs (last 3 days) exist

**Step 4: Final verification**

Run: `python .claude/hooks/pushover-hook/diagnose.py`
Expected: All checks pass

**Step 5: Final commit**

```bash
git add .
git commit -m "test(log): verify integration testing"
```

---

## Implementation Notes

### Behavior
- Cleanup runs on every script startup (minimal overhead)
- Only processes files matching `debug.YYYY-MM-DD.log` pattern
- Current `debug.log` is never deleted
- Failures are silent to not break hook functionality

### Edge Cases Handled
- Log directory doesn't exist: Silent skip
- Invalid filename format: Skip file
- Invalid date in filename: Skip file
- Delete permission error: Log and continue

### Future Enhancements (Out of Scope)
- Configurable retention period via environment variable
- Max file size rotation (rotate by size, not just date)
- Compressed archive for old logs

---

## References

- @superpowers:executing-plans - For step-by-step implementation
- Original design discussion in brainstorming session
- Existing log functions: `get_log_path()`, `log()` in pushover-notify.py:19-34
