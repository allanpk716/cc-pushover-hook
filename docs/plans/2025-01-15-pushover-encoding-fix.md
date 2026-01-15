# Pushover Encoding Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix character encoding issues causing Chinese text to display as garbled characters and empty notification bodies showing `{}` in Pushover notifications on Windows.

**Architecture:** Force UTF-8 encoding at Python entry point using `sys.stdin.reconfigure(encoding='utf-8')` and `PYTHONIOENCODING=utf-8` environment variable. Improve empty notification body handling to show meaningful messages instead of `{}`.

**Tech Stack:** Python 3.7+, subprocess, curl, Windows CMD/PowerShell

---

## Context: The Problem

On Windows, when Claude Code sends hook data to the Python script:
1. Claude Code outputs UTF-8 JSON to stdin
2. Windows console defaults to CP936/GBK (Chinese locale) or CP1252 (English locale)
3. Python reads stdin with wrong encoding → garbled characters
4. Empty notification body dicts (`{}`) display as literal `{}` string

**Root causes:**
- No explicit UTF-8 configuration for stdin
- Empty dict handling shows literal `{}` instead of helpful message

---

## Task 1: Add UTF-8 stdin reconfiguration

**Files:**
- Modify: `.claude/hooks/pushover-notify.py:253-257`

**Step 1: Read current main() function**

```bash
# View current code around line 253-257
head -n 260 .claude/hooks/pushover-notify.py | tail -n 10
```

**Step 2: Add stdin encoding reconfiguration**

After line 255 (log("=" * 60)), BEFORE line 256 (log(f"Hook script started...")), add:

```python
    # Force UTF-8 encoding for stdin on all platforms (Windows encoding fix)
    if hasattr(sys.stdin, 'reconfigure'):
        sys.stdin.reconfigure(encoding='utf-8')
        log(f"Stdin encoding configured: {sys.stdin.encoding}")
    else:
        log("WARNING: stdin.reconfigure not available (Python < 3.7)")
```

**Step 3: Verify file syntax**

```bash
python -m py_compile .claude/hooks/pushover-notify.py
```

Expected: No output (success)

**Step 4: Commit**

```bash
git add .claude/hooks/pushover-notify.py
git commit -m "fix(hook): add UTF-8 stdin reconfiguration for Windows encoding support"
```

---

## Task 2: Improve empty notification body handling

**Files:**
- Modify: `.claude/hooks/pushover-notify.py:343-349`

**Step 1: Read current notification body handling**

```bash
# View current code around line 343-349
sed -n '343,349p' .claude/hooks/pushover-notify.py
```

**Step 2: Replace with improved handling**

Replace lines 343-349 with:

```python
        # Build message from notification body
        if isinstance(notification_body, dict):
            # Extract meaningful content, skip empty dicts
            if notification_body:
                details = notification_body.get("text", json.dumps(notification_body, ensure_ascii=False))
            else:
                details = "No additional details provided"
        else:
            details = str(notification_body) if notification_body else "No additional details provided"
```

**Step 3: Verify file syntax**

```bash
python -m py_compile .claude/hooks/pushover-notify.py
```

Expected: No output (success)

**Step 4: Commit**

```bash
git add .claude/hooks/pushover-notify.py
git commit -m "fix(hook): improve empty notification body handling"
```

---

## Task 3: Add encoding debug logging

**Files:**
- Modify: `.claude/hooks/pushover-notify.py:318-323`

**Step 1: Read current Stop event message construction**

```bash
# View current code around line 318-323
sed -n '318,323p' .claude/hooks/pushover-notify.py
```

**Step 2: Add encoding debug log**

After line 323 (send_pushover call), add:

```python
        log(f"Message stats: chars={len(message)}, bytes={len(message.encode('utf-8'))}")
```

**Step 3: Verify file syntax**

```bash
python -m py_compile .claude/hooks/pushover-notify.py
```

Expected: No output (success)

**Step 4: Commit**

```bash
git add .claude/hooks/pushover-notify.py
git commit -m "feat(hook): add encoding debug logging"
```

---

## Task 4: Add encoding environment variable to hook command template

**Files:**
- Modify: `install.py` (update the hook command template)
- Create: `templates/settings.json.template` (example configuration)

**Step 1: Read current install.py to find hook command template**

```bash
# Find where hook command is set
grep -n "command.*pushover-notify" install.py
```

**Step 2: Update install.py hook command**

Find the line that sets the hook command (around the hook configuration section) and modify it to include the encoding environment variable.

For Windows:
```python
"command": f"set PYTHONIOENCODING=utf-8&& \"{hook_dir}/pushover-notify.py\""
```

For Linux/macOS (can also include for consistency):
```python
"command": f"PYTHONIOENCODING=utf-8 \"{hook_dir}/pushover-notify.py\""
```

**Note:** The exact implementation depends on how install.py currently generates the settings.json. You may need to:
- Add platform detection
- Update the command string template
- Ensure proper path handling

**Step 3: Create settings.json template**

Create `templates/settings.json.template`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "set PYTHONIOENCODING=utf-8&& \"$CLAUDE_PROJECT_DIR/.claude/hooks/pushover-notify.py\""
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "set PYTHONIOENCODING=utf-8&& \"$CLAUDE_PROJECT_DIR/.claude/hooks/pushover-notify.py\""
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
            "command": "set PYTHONIOENCODING=utf-8&& \"$CLAUDE_PROJECT_DIR/.claude/hooks/pushover-notify.py\""
          }
        ]
      }
    ]
  }
}
```

**Step 4: Commit**

```bash
git add install.py templates/settings.json.template
git commit -m "feat(installer): add PYTHONIOENCODING to hook command for Windows UTF-8 support"
```

---

## Task 5: Add Chinese character test to test-pushover.py

**Files:**
- Modify: `.claude/hooks/test-pushover.py`

**Step 1: Read current test-pushover.py**

```bash
# Find send_test_notification function
grep -n "def send_test_notification" .claude/hooks/test-pushover.py
```

**Step 2: Add new test function**

Add after the `send_test_notification` function (after line 187):

```python
def test_chinese_encoding(token: str, user: str) -> bool:
    """Test Chinese character encoding in notifications."""
    print_header("Step 3b: Testing Chinese Character Encoding")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    title = "编码测试 (Encoding Test)"
    message = f"中文测试：你来测试最新开发的 rustdesk 服务器协议的扫描功能\\nTime: {timestamp}\\nIP: 116.62.8.4"

    print_info(f"Title: {title}")
    print_info(f"Message: {message}")
    print_info(f"Expected: Chinese characters should display correctly")

    response_file = Path("pushover_response_chinese.txt")

    try:
        cmd = [
            "curl",
            "-s",
            "-o", str(response_file),
            "-w", "%{http_code}",
            "https://api.pushover.net/1/messages.json",
            "--data-urlencode", f"token={token}",
            "--data-urlencode", f"user={user}",
            "--data-urlencode", f"title={title}",
            "--data-urlencode", f"message={message}",
            "-d", "priority=0",
        ]

        print_info("Sending test notification with Chinese characters...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        http_code = result.stdout.strip()
        print_info(f"HTTP Status Code: {http_code}")

        if response_file.exists():
            response_body = response_file.read_text(encoding="utf-8")
            response_file.unlink()
            print_info(f"Response body: {response_body}")

            try:
                response_json = json.loads(response_body)
                if response_json.get("status") == 1:
                    print_success("Chinese encoding test passed!")
                    print_info("Please verify on your device that characters display correctly")
                    return True
                else:
                    print_error("Notification failed")
                    if "errors" in response_json:
                        for error in response_json["errors"]:
                            print_error(f"API Error: {error}")
                    return False
            except json.JSONDecodeError:
                print_warning("Could not parse response as JSON")
        else:
            print_warning("No response body captured")

        if http_code == "200":
            print_success("Notification sent (HTTP 200)")
            return True
        else:
            print_error(f"Unexpected HTTP code: {http_code}")
            return False

    except subprocess.TimeoutExpired:
        print_error("Request timed out")
        response_file.unlink(missing_ok=True)
        return False
    except Exception as e:
        print_error(f"Exception: {e}")
        response_file.unlink(missing_ok=True)
        return False


def test_empty_notification_body(token: str, user: str) -> bool:
    """Test empty notification body handling."""
    print_header("Step 3c: Testing Empty Notification Body")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    title = "Empty Body Test"
    message = f"Session: test-session-{timestamp}\\nType: test_notification\\nNo additional details provided"

    print_info(f"Title: {title}")
    print_info(f"Message: {message}")
    print_info("Expected: Should NOT show literal '{}'")

    response_file = Path("pushover_response_empty.txt")

    try:
        cmd = [
            "curl",
            "-s",
            "-o", str(response_file),
            "-w", "%{http_code}",
            "https://api.pushover.net/1/messages.json",
            "--data-urlencode", f"token={token}",
            "--data-urlencode", f"user={user}",
            "--data-urlencode", f"title={title}",
            "--data-urlencode", f"message={message}",
            "-d", "priority=0",
        ]

        print_info("Sending test notification simulating empty body...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        http_code = result.stdout.strip()
        print_info(f"HTTP Status Code: {http_code}")

        if response_file.exists():
            response_body = response_file.read_text(encoding="utf-8")
            response_file.unlink()

            try:
                response_json = json.loads(response_body)
                if response_json.get("status") == 1:
                    print_success("Empty body test passed!")
                    return True
                else:
                    print_error("Notification failed")
                    return False
            except json.JSONDecodeError:
                print_warning("Could not parse response as JSON")
        else:
            print_warning("No response body captured")

        return http_code == "200"

    except subprocess.TimeoutExpired:
        print_error("Request timed out")
        response_file.unlink(missing_ok=True)
        return False
    except Exception as e:
        print_error(f"Exception: {e}")
        response_file.unlink(missing_ok=True)
        return False
```

**Step 3: Update main() to call new tests**

Find the main() function and add after the send_test_notification call:

```python
    # Send test notification
    notification_ok = send_test_notification(env_results["token"], env_results["user"])
    print()

    # Additional encoding tests
    if notification_ok:
        chinese_ok = test_chinese_encoding(env_results["token"], env_results["user"])
        print()
        empty_ok = test_empty_notification_body(env_results["token"], env_results["user"])
        print()

        # Update final result
        notification_ok = chinese_ok and empty_ok
```

**Step 4: Verify file syntax**

```bash
python -m py_compile .claude/hooks/test-pushover.py
```

Expected: No output (success)

**Step 5: Commit**

```bash
git add .claude/hooks/test-pushover.py
git commit -m "test: add Chinese encoding and empty body tests"
```

---

## Task 6: Create manual test script

**Files:**
- Create: `.claude/hooks/test-encoding-manual.py`

**Step 1: Create manual test script**

```python
#!/usr/bin/env python3
"""
Manual encoding test script.

Simulates hook events to verify UTF-8 encoding works correctly.
"""

import json
import subprocess
import sys
from pathlib import Path

def test_stop_event_with_chinese():
    """Test Stop event with Chinese summary."""
    hook_script = Path(__file__).parent / "pushover-notify.py"

    test_data = {
        "hook_event_name": "Stop",
        "session_id": "test-encoding-session",
        "cwd": str(Path.cwd()),
    }

    # Simulate Chinese summary in cache
    cache_dir = Path.cwd() / ".claude" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_file = cache_dir / "session-test-encoding-session.jsonl"
    with open(cache_file, "w", encoding="utf-8") as f:
        entry = {
            "type": "user_prompt_submit",
            "prompt": "你来测试最新开发的 rustdesk 服务器协议的扫描功能，我已经部署有一台服务器IP：116.62.8.4",
            "timestamp": "2025-01-15T12:00:00Z",
        }
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Run hook script
    result = subprocess.run(
        [sys.executable, str(hook_script)],
        input=json.dumps(test_data, ensure_ascii=False),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    print("=== Stop Event Test (Chinese) ===")
    print(f"Return code: {result.returncode}")
    print(f"Stdout: {result.stdout}")
    print(f"Stderr: {result.stderr}")

    # Clean up
    cache_file.unlink(missing_ok=True)

    return result.returncode == 0


def test_notification_event_empty_body():
    """Test Notification event with empty body."""
    hook_script = Path(__file__).parent / "pushover-notify.py"

    test_data = {
        "hook_event_name": "Notification",
        "session_id": "test-empty-body-session",
        "cwd": str(Path.cwd()),
        "type": "permission_prompt",
        "body": {},  # Empty dict
    }

    # Run hook script
    result = subprocess.run(
        [sys.executable, str(hook_script)],
        input=json.dumps(test_data, ensure_ascii=False),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    print("=== Notification Event Test (Empty Body) ===")
    print(f"Return code: {result.returncode}")
    print(f"Stdout: {result.stdout}")
    print(f"Stderr: {result.stderr}")

    return result.returncode == 0


if __name__ == "__main__":
    print("Running manual encoding tests...")
    print()

    test1 = test_stop_event_with_chinese()
    print()
    test2 = test_notification_event_empty_body()
    print()

    if test1 and test2:
        print("All manual tests passed!")
        sys.exit(0)
    else:
        print("Some tests failed!")
        sys.exit(1)
```

**Step 2: Make executable (Linux/macOS only)**

```bash
chmod +x .claude/hooks/test-encoding-manual.py
```

**Step 3: Run manual test**

```bash
cd .claude/hooks && python test-encoding-manual.py
```

**Step 4: Commit**

```bash
git add .claude/hooks/test-encoding-manual.py
git commit -m "test: add manual encoding test script"
```

---

## Task 7: Update README with encoding troubleshooting

**Files:**
- Modify: `README.md`

**Step 1: Read current README**

```bash
# View current README structure
grep -n "^##" README.md
```

**Step 2: Add troubleshooting section**

Add after the existing content:

```markdown

## Encoding Troubleshooting

### Chinese characters showing as garbled text

If Chinese or other non-ASCII characters appear corrupted in notifications:

1. **Verify Python version** - Requires Python 3.7+ for `sys.stdin.reconfigure()`
   ```bash
   python --version
   ```

2. **Check hook command includes encoding variable** - In `.claude/settings.json`:
   ```json
   "command": "set PYTHONIOENCODING=utf-8&& \"$CLAUDE_PROJECT_DIR/.claude/hooks/pushover-notify.py\""
   ```

3. **Run encoding test**:
   ```bash
   cd .claude/hooks && python test-encoding-manual.py
   ```

4. **Check debug log** - View `.claude/hooks/debug.log` for:
   ```
   [timestamp] Stdin encoding configured: utf-8
   [timestamp] Message stats: chars=XX, bytes=YY
   ```

### Empty notification shows `{}`

If notification body shows literal `{}` instead of a meaningful message:

1. This is fixed in the updated script
2. Update to latest version: `git pull` or reinstall hooks
3. Verify `pushover-notify.py` contains the improved body handling (lines ~343-349)

### Windows-specific notes

- Windows console defaults to CP936/GBK (Chinese) or CP1252 (English)
- The `PYTHONIOENCODING=utf-8` override is critical on Windows
- CMD and PowerShell both support the `set VAR=value&& command` syntax
```

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add encoding troubleshooting section to README"
```

---

## Task 8: Create design documentation

**Files:**
- Create: `docs/plans/2025-01-15-pushover-encoding-fix-design.md`

**Step 1: Create design document**

```markdown
# Pushover Encoding Fix Design

**Date:** 2025-01-15
**Status:** Implemented

## Problem Statement

On Windows, Pushover notifications had two issues:

1. **Character encoding corruption**: Chinese text displayed as garbled characters
   - Original: "你来测试最新开发的 rustdesk 服务器协议的扫描功能"
   - Displayed: "浣犳潵娴嬭瘯鏈�鏂板紑鍙戠殑 rustdesk 鏈嶅姟鍣ㄥ崗璁�"

2. **Empty notification body**: Showed literal `{}` instead of helpful message

## Root Cause Analysis

### Issue 1: Encoding Mismatch

- Claude Code outputs UTF-8 JSON to stdin
- Windows console defaults to CP936/GBK (Chinese locale) or CP1252 (English)
- Python reads stdin with wrong encoding → mojibake (garbled text)

The garbled characters show a classic UTF-8 → CP936 reinterpretation pattern.

### Issue 2: Empty Dict Handling

```python
notification_body = hook_input.get("body", {})  # Returns {} if missing
message = str(notification_body)  # Results in literal "{}"
```

## Solution Architecture

```
Claude Code (UTF-8)
    ↓
Hook command: PYTHONIOENCODING=utf-8
    ↓
Python: sys.stdin.reconfigure(encoding='utf-8')
    ↓
stdin.read() → correct UTF-8 string
    ↓
JSON parsing with proper Unicode
    ↓
Message construction preserves characters
    ↓
curl --data-urlencode → Pushover API (UTF-8)
    ↓
Correct display on device
```

## Implementation

### 1. stdin Encoding Configuration

```python
# At start of main()
if hasattr(sys.stdin, 'reconfigure'):
    sys.stdin.reconfigure(encoding='utf-8')
    log(f"Stdin encoding configured: {sys.stdin.encoding}")
```

### 2. Environment Variable Wrapper

```json
"command": "set PYTHONIOENCODING=utf-8&& \"$CLAUDE_PROJECT_DIR/.claude/hooks/pushover-notify.py\""
```

### 3. Empty Body Handling

```python
if isinstance(notification_body, dict):
    if notification_body:
        details = notification_body.get("text", json.dumps(notification_body, ensure_ascii=False))
    else:
        details = "No additional details provided"
else:
    details = str(notification_body) if notification_body else "No additional details provided"
```

## Testing

- Automated: `python .claude/hooks/test-pushover.py`
- Manual: `python .claude/hooks/test-encoding-manual.py`
- Verification: Check debug.log for encoding confirmation

## Platform Compatibility

| Platform | Status | Notes |
|----------|--------|-------|
| Windows (Chinese locale) | ✅ Fixed | Requires PYTHONIOENCODING |
| Windows (English locale) | ✅ Fixed | Requires PYTHONIOENCODING |
| Linux | ✅ Compatible | UTF-8 by default |
| macOS | ✅ Compatible | UTF-8 by default |
```

**Step 2: Commit**

```bash
git add docs/plans/2025-01-15-pushover-encoding-fix-design.md
git commit -m "docs: add encoding fix design documentation"
```

---

## Task 9: Run full test suite

**Files:**
- Test: `.claude/hooks/test-pushover.py`
- Test: `.claude/hooks/test-encoding-manual.py`
- Log: `.claude/hooks/debug.log`

**Step 1: Run automated test**

```bash
python .claude/hooks/test-pushover.py
```

Expected: All checks pass, Chinese characters display correctly

**Step 2: Run manual encoding test**

```bash
cd .claude/hooks && python test-encoding-manual.py
```

Expected: All manual tests pass

**Step 3: Check debug log**

```bash
# View last 50 lines of debug log
tail -n 50 .claude/hooks/debug.log
```

Expected output:
```
[timestamp] Stdin encoding configured: utf-8
[timestamp] Message stats: chars=XX, bytes=YY
```

**Step 4: Trigger real hook test**

In a Claude Code session with the hook configured:
1. Submit a task with Chinese text
2. Wait for Stop event
3. Verify notification shows correct Chinese characters

**Step 5: Verify empty body notification**

1. Trigger a permission prompt in Claude Code
2. Verify notification shows "No additional details provided" instead of `{}`

---

## Task 10: Final verification and tag

**Step 1: Review all changes**

```bash
git diff main
```

**Step 2: Run all tests one more time**

```bash
python .claude/hooks/test-pushover.py && cd .claude/hooks && python test-encoding-manual.py
```

**Step 3: Update version (if applicable)**

If there's a version in README or install.py, update it:
```bash
# Update version to 1.1.0 or similar
```

**Step 4: Create release tag**

```bash
git tag -a v1.1.0 -m "Fix encoding issues for Chinese characters and empty notification bodies"
git push origin v1.1.0
```

**Step 5: Update CHANGELOG (if exists)**

```bash
# Add entry to CHANGELOG.md
```

---

## Verification Checklist

After implementation, verify:

- [ ] Chinese characters display correctly in Pushover notifications
- [ ] Empty notification body shows "No additional details provided"
- [ ] Debug log shows "Stdin encoding configured: utf-8"
- [ ] All automated tests pass
- [ ] All manual tests pass
- [ ] Documentation updated
- [ ] Works on Windows (both Chinese and English locales)
- [ ] No regression on Linux/macOS

---

## Relevant Skills

- @superpowers:executing-plans - Use this skill to implement the plan
- @superpowers:verification-before-completion - Run verification commands before claiming completion
- @superpowers:test-driven-development - Write tests first for new functionality
