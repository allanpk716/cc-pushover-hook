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

**Requirements**: Python 3.7+ (required for `sys.stdin.reconfigure()`)

```python
# At start of main()
if hasattr(sys.stdin, 'reconfigure'):
    sys.stdin.reconfigure(encoding='utf-8')
    log(f"Stdin encoding configured: {sys.stdin.encoding}")
else:
    log("WARNING: stdin.reconfigure not available (Python < 3.7)")
```

### 2. Environment Variable Wrapper

**Note**: The installer generates platform-specific commands. The examples below show the actual commands generated:

**Windows**:
```json
"command": "set PYTHONIOENCODING=utf-8&& python \"C:\\absolute\\path\\to\\.claude\\hooks\\pushover-notify.py\""
```

**Linux/macOS**:
```json
"command": "PYTHONIOENCODING=utf-8 \"/absolute/path/to/.claude/hooks/pushover-notify.py\""
```

The installer uses absolute paths instead of `$CLAUDE_PROJECT_DIR` due to Windows environment variable expansion issues (see GitHub issues #6023, #5648).

### 3. Windows Path Handling

**Problem**: Windows paths in JSON contain backslashes that break JSON parsing.

**Solution**: Escape backslashes before JSON parsing.

```python
# Fix Windows paths in JSON (backslashes need to be escaped)
stdin_data = stdin_data.replace("\\", "\\\\")

try:
    hook_input = json.loads(stdin_data)
    log(f"JSON parsed successfully")
except json.JSONDecodeError as e:
    log(f"ERROR: JSON decode failed: {e}")
    return
```

This ensures that paths like `C:\Users\Name\project` become `C:\\Users\\Name\\project` in the JSON string, allowing valid parsing.

### 4. Empty Body Handling

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
| Python Version | ✅ Required | Python 3.7+ (for stdin.reconfigure) |
| Windows (Chinese locale) | ✅ Fixed | Requires PYTHONIOENCODING |
| Windows (English locale) | ✅ Fixed | Requires PYTHONIOENCODING |
| Linux | ✅ Compatible | UTF-8 by default |
| macOS | ✅ Compatible | UTF-8 by default |
