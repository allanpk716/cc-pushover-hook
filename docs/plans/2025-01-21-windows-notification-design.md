# Windows Native Notification Support - Design Document

## Overview

Add Windows 10/11 native notification support to the existing Pushover Hook. Notifications send via both channels by default. Users can disable each channel independently with flag files.

## Requirements

- Support Windows 10/11 native notifications
- Send via both Pushover and Windows by default
- Allow independent disable: `.no-pushover` for Pushover, `.no-windows` for Windows
- Auto-upgrade must handle existing installations
- No external Python dependencies

## Architecture

### Notification Flow

```
Hook Trigger
    |
    v
Check Disable Flags (.no-pushover, .no-windows)
    |
    +--> Pushover enabled? --> Send Pushover
    |
    +--> Windows enabled? --> Send Windows
    |
    v
Log Results
```

### Disable File Behavior

| File | Effect |
|------|--------|
| `.no-pushover` | Disables Pushover only |
| `.no-windows` | Disables Windows only |
| Both files | Disables all notifications |
| Neither file | Both channels active |

## Implementation

### Windows Notification Function

Use PowerShell with Windows.UI.Notifications namespace:

```python
def send_windows_notification(title: str, message: str) -> bool:
    """Send Windows 10/11 notification via PowerShell."""
    title_escaped = title.replace("'", "''")
    message_escaped = message.replace("'", "''").replace("\n", "`n")

    ps_script = f'''
    Add-Type -AssemblyName Windows.UI.Notifications
    Add-Type -AssemblyName Windows.Data.Xml.Dom

    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml([string]::Format('
        <toast><visual><binding template="ToastText02">
            <text id="1">{{0}}</text>
            <text id="2">{{1}}</text>
        </binding></visual></toast>', '{title_escaped}', '{message_escaped}'))

    $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
    $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("ClaudeCode")
    $notifier.Show($toast)
    '''

    result = subprocess.run(
        ["powershell", "-Command", ps_script],
        capture_output=True,
        timeout=5
    )

    return result.returncode == 0
```

### Refactored Send Function

```python
def send_notifications(title: str, message: str, priority: int = 0, cwd: str = "") -> dict:
    """Send notifications via enabled channels."""
    results = {"pushover": False, "windows": False}

    pushover_disabled = cwd and is_notification_disabled(cwd)
    windows_disabled = cwd and is_windows_notification_disabled(cwd)

    if pushover_disabled and windows_disabled:
        log("All notifications disabled")
        return results

    if not pushover_disabled:
        results["pushover"] = _send_pushover_internal(title, message, priority)

    if not windows_disabled and sys.platform == "win32":
        results["windows"] = send_windows_notification(title, message)

    return results
```

### Disable Check Function

```python
def is_windows_notification_disabled(cwd: str) -> bool:
    """Check if Windows notifications are disabled."""
    silent_file = Path(cwd) / ".no-windows"
    disabled = silent_file.exists()
    if disabled:
        log(f"Windows notifications disabled: {silent_file} exists")
    return disabled
```

## Auto-Upgrade Changes

### Cleanup Old Disable Files

Modify `install.py` to remove old `.no-pushover` files from `.claude/` directory:

```python
# In copy_hook_files() method
old_silent_file = self.target_dir / ".claude" / ".no-pushover"
if old_silent_file.exists():
    try:
        old_silent_file.unlink()
        print(f"[OK] Removed old disable flag: .claude/.no-pushover")
    except Exception as e:
        print(f"[WARN] Failed to remove {old_silent_file.name}: {e}")
```

### Documentation Updates

Add `.no-windows` instructions to README:

```bash
# Disable Windows notifications
type nul > .no-windows

# Re-enable Windows notifications
del .no-windows
```

## Error Handling

Windows notification failures must not block the entire flow:

| Scenario | Pushover | Windows | Behavior |
|----------|----------|---------|----------|
| Both available | Sent | Sent | Success logged |
| Pushover fails | Failed | Sent | Pushover error logged |
| Windows fails | Sent | Failed | Windows error logged |
| Both fail | Failed | Failed | Both errors logged |
| Pushover disabled | Skipped | Sent | Disable flag logged |
| Windows disabled | Sent | Skipped | Disable flag logged |

## Testing

### New Test Script: `test-windows-notification.py`

- Test Windows notification send
- Verify `.no-windows` disable function
- Verify non-Windows platform skip logic

### Integration Tests

- Dual channel send test
- Disable file combination scenarios
- Upgrade file cleanup verification

## File Changes

| File | Change |
|------|--------|
| `pushover-notify.py` | Add Windows notification functions, refactor send logic |
| `install.py` | Add cleanup for old disable files |
| `README.md` | Document `.no-windows` usage |
| `diagnose.py` | Add Windows channel detection |
| `test-windows-notification.py` | New test script |
