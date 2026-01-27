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
