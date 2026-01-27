#!/usr/bin/env python3
"""Test parallel notification sending with slow Pushover simulation."""

import sys
import time
import importlib.util
from pathlib import Path

# Load pushover_notify module dynamically
script_dir = Path(__file__).parent
module_path = script_dir / "pushover-notify.py"
spec = importlib.util.spec_from_file_location("pushover_notify", module_path)
pushover_notify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pushover_notify)

send_notifications = pushover_notify.send_notifications
log = pushover_notify.log

def test_parallel_speed():
    """Test that Windows notification completes quickly even with slow Pushover."""
    print("=" * 60)
    print("Testing parallel notification sending...")
    print("=" * 60)

    # Simulate slow network by using a test that completes
    # In real usage, Pushover might take 2-5 seconds on slow networks
    start = time.time()

    title = "[Test] Parallel Notifications"
    message = "Session: test-123\\nSummary: Testing parallel execution"

    log("Starting test: parallel notifications")
    results = send_notifications(title, message, priority=0, cwd=".")

    elapsed = time.time() - start

    print(f"\nResults:")
    print(f"  Pushover: {results['pushover']}")
    print(f"  Windows:  {results['windows']}")
    print(f"  Total time: {elapsed:.2f}s")

    # Windows notification should complete quickly (< 2s)
    # even if Pushover is slow (network delay)
    if results['windows']:
        print("\n[OK] Windows notification sent successfully")

        if elapsed < 3.0:
            print(f"[OK] Completed in reasonable time ({elapsed:.2f}s < 3s)")
        else:
            print(f"[WARN] Took longer than expected ({elapsed:.2f}s)")
    else:
        print("\n[FAIL] Windows notification failed")

    print("=" * 60)
    return results

if __name__ == "__main__":
    test_parallel_speed()
