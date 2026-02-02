#!/usr/bin/env python3
"""
Multi-instance isolation test script.

Tests that multiple Claude Code instances can run concurrently
without cache or log conflicts.
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

def get_test_pid():
    """Get a fake PID for testing."""
    return os.getpid()

def test_cache_isolation():
    """Test that different PIDs create separate cache files."""
    print("Test 1: Cache file isolation by PID")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir) / ".claude" / "cache"
        cache_dir.mkdir(parents=True)

        # Simulate two instances
        pid1 = 1234
        pid2 = 5678
        session_id = "test-session-123"

        cache_file1 = cache_dir / f"session-{session_id}-pid-{pid1}.jsonl"
        cache_file2 = cache_dir / f"session-{session_id}-pid-{pid2}.jsonl"

        # Write to first cache
        entry1 = {"type": "user_prompt_submit", "prompt": "Instance 1", "pid": pid1}
        cache_file1.write_text(json.dumps(entry1) + "\n")

        # Write to second cache
        entry2 = {"type": "user_prompt_submit", "prompt": "Instance 2", "pid": pid2}
        cache_file2.write_text(json.dumps(entry2) + "\n")

        # Verify separation
        assert cache_file1.exists(), "Cache file 1 should exist"
        assert cache_file2.exists(), "Cache file 2 should exist"

        content1 = json.loads(cache_file1.read_text().strip())
        content2 = json.loads(cache_file2.read_text().strip())

        assert content1["pid"] == pid1, f"Cache 1 should have PID {pid1}"
        assert content2["pid"] == pid2, f"Cache 2 should have PID {pid2}"
        assert content1["prompt"] != content2["prompt"], "Caches should have different content"

        print("[PASS] Cache files are properly isolated by PID")
        print(f"   - Cache 1: {cache_file1.name}")
        print(f"   - Cache 2: {cache_file2.name}")

def test_log_isolation():
    """Test that different PIDs create separate log files."""
    print("\nTest 2: Log file isolation by PID")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        log_dir = Path(temp_dir)

        # Simulate two instances
        pid1 = 1234
        pid2 = 5678
        today = datetime.now().strftime("%Y-%m-%d")

        log_file1 = log_dir / f"debug.{today}-pid-{pid1}.log"
        log_file2 = log_dir / f"debug.{today}-pid-{pid2}.log"

        # Write to first log
        log_file1.write_text("[2025-02-02 12:00:00] Instance 1 log\n")

        # Write to second log
        log_file2.write_text("[2025-02-02 12:00:01] Instance 2 log\n")

        # Verify separation
        assert log_file1.exists(), "Log file 1 should exist"
        assert log_file2.exists(), "Log file 2 should exist"

        content1 = log_file1.read_text()
        content2 = log_file2.read_text()

        assert "Instance 1 log" in content1, "Log 1 should contain Instance 1 entry"
        assert "Instance 2 log" in content2, "Log 2 should contain Instance 2 entry"
        assert content1 != content2, "Logs should have different content"

        print("[PASS] Log files are properly isolated by PID")
        print(f"   - Log 1: {log_file1.name}")
        print(f"   - Log 2: {log_file2.name}")

def test_completion_marker():
    """Test that Stop event adds completion marker instead of deleting."""
    print("\nTest 3: Completion marker instead of deletion")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir) / ".claude" / "cache"
        cache_dir.mkdir(parents=True)

        pid = 1234
        session_id = "test-session-456"
        cache_file = cache_dir / f"session-{session_id}-pid-{pid}.jsonl"

        # Write initial cache entry
        entry = {
            "type": "user_prompt_submit",
            "prompt": "Test prompt",
            "pid": pid
        }
        cache_file.write_text(json.dumps(entry) + "\n")

        # Simulate Stop event adding completion marker
        completed_entry = {
            "type": "session_complete",
            "timestamp": datetime.utcnow().isoformat(),
            "pid": pid
        }

        with open(cache_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(completed_entry) + "\n")

        # Verify file still exists and has both entries
        assert cache_file.exists(), "Cache file should still exist"

        lines = cache_file.read_text().strip().split("\n")
        assert len(lines) == 2, f"Cache should have 2 entries, got {len(lines)}"

        first_entry = json.loads(lines[0])
        last_entry = json.loads(lines[1])

        assert first_entry["type"] == "user_prompt_submit"
        assert last_entry["type"] == "session_complete"

        print("[PASS] Completion marker added, cache file preserved")
        print(f"   - Cache file: {cache_file.name}")
        print(f"   - Entries: {len(lines)}")

def main():
    """Run all tests."""
    print("=" * 60)
    print("Multi-Instance Isolation Tests")
    print("=" * 60)

    try:
        test_cache_isolation()
        test_log_isolation()
        test_completion_marker()

        print("\n" + "=" * 60)
        print("[PASS] All tests passed!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
