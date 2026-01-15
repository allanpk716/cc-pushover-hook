#!/usr/bin/env python3
"""
Pushover notification hook for Claude Code.

Sends notifications when:
- Task completes (Stop hook)
- Attention needed (Notification hook for permission/idle prompts)
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def send_pushover(title: str, message: str, priority: int = 0) -> bool:
    """
    Send a notification via Pushover API using curl.

    Args:
        title: Notification title
        message: Notification message body
        priority: Message priority (-2 to 2, default 0)

    Returns:
        True if successful, False otherwise
    """
    token = os.environ.get("PUSHOVER_TOKEN")
    user = os.environ.get("PUSHOVER_USER")

    if not token or not user:
        return False

    try:
        result = subprocess.run(
            [
                "curl",
                "-s",
                "-o",
                "/dev/null",
                "-w",
                "%{http_code}",
                "https://api.pushover.net/1/messages.json",
                "-d",
                f"token={token}",
                "-d",
                f"user={user}",
                "-d",
                f"title={title}",
                "-d",
                f"message={message}",
                "-d",
                f"priority={priority}",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0 and "200" in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False


def get_project_name(cwd: str) -> str:
    """
    Extract project name from working directory path.

    Args:
        cwd: Current working directory

    Returns:
        Project name or fallback string
    """
    try:
        return os.path.basename(os.path.normpath(cwd))
    except Exception:
        return "Unknown Project"


def summarize_conversation(session_id: str, cwd: str) -> str:
    """
    Generate a summary of the conversation using Claude CLI.

    Args:
        session_id: The session identifier
        cwd: Current working directory

    Returns:
        Summary string or fallback message
    """
    cache_dir = Path(cwd) / ".claude" / "cache"
    cache_file = cache_dir / f"session-{session_id}.jsonl"

    # Fallback: extract last user message
    fallback_summary = "Task completed"

    if not cache_file.exists():
        return fallback_summary

    try:
        lines = cache_file.read_text(encoding="utf-8").strip().split("\n")
        if not lines or lines == [""]:
            return fallback_summary

        # Get last user message as fallback
        for line in reversed(lines):
            try:
                data = json.loads(line)
                if data.get("type") == "user_prompt_submit":
                    content = data.get("prompt", "")
                    if content:
                        # Truncate to reasonable length
                        fallback_summary = (
                            content[:100] + "..." if len(content) > 100 else content
                        )
                        break
            except json.JSONDecodeError:
                continue

        # Try to use Claude CLI for summarization
        try:
            conversation_text = "\n".join(lines)
            prompt = f"""Summarize this conversation in one concise sentence (max 15 words):

{conversation_text}

Summary:"""

            result = subprocess.run(
                ["claude", "-p", prompt],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=cwd,
            )

            if result.returncode == 0 and result.stdout.strip():
                summary = result.stdout.strip()
                if len(summary) < 200:
                    return summary

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass

        return fallback_summary

    except Exception:
        return fallback_summary


def main() -> None:
    """Main hook handler."""
    # Read hook event from stdin
    try:
        hook_input = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return

    hook_event = hook_input.get("hook_event_name", "")
    session_id = hook_input.get("session_id", "")
    cwd = hook_input.get("cwd", os.getcwd())

    if not session_id:
        return

    if hook_event == "UserPromptSubmit":
        # Record user input to cache
        cache_dir = Path(cwd) / ".claude" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        cache_file = cache_dir / f"session-{session_id}.jsonl"

        try:
            entry = {
                "type": "user_prompt_submit",
                "prompt": hook_input.get("prompt", ""),
                "timestamp": hook_input.get("timestamp", ""),
            }

            with open(cache_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except (OSError, IOError):
            pass

    elif hook_event == "Stop":
        # Send task completion notification
        project_name = get_project_name(cwd)
        summary = summarize_conversation(session_id, cwd)

        title = f"[{project_name}] Task Complete"
        message = f"Session: {session_id}\\nSummary: {summary}"

        send_pushover(title, message, priority=0)

        # Clean up cache
        cache_file = Path(cwd) / ".claude" / "cache" / f"session-{session_id}.jsonl"
        try:
            cache_file.unlink(missing_ok=True)
        except OSError:
            pass

    elif hook_event == "Notification":
        # Send attention needed notification
        notification_type = hook_input.get("type", "notification")
        notification_body = hook_input.get("body", {})

        project_name = get_project_name(cwd)

        title = f"[{project_name}] Attention Needed"

        # Build message from notification body
        if isinstance(notification_body, dict):
            details = notification_body.get("text", str(notification_body))
        else:
            details = str(notification_body)

        message = f"Session: {session_id}\\nType: {notification_type}\\n{details}"

        # Higher priority for attention needed
        send_pushover(title, message, priority=1)


if __name__ == "__main__":
    main()
