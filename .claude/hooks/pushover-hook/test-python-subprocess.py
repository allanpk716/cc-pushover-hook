import subprocess
import sys

title = "Python Subprocess Test"
message = "Testing from Python"

title_escaped = title.replace("'", "''")
message_escaped = message.replace("'", "''")

ps_script = f'''
try {{
    Add-Type -AssemblyName System.Runtime.WindowsRuntime -ErrorAction Stop
    $null = [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
    $null = [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime]
    $template = @"
<toast><visual><binding template="ToastText02">
    <text id="1">{title_escaped}</text>
    <text id="2">{message_escaped}</text>
</binding></visual></toast>
"@
    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml($template)
    $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("ClaudeCode").Show($toast)
    exit 0
}} catch {{
    Write-Host "ERROR: $($_.Exception.Message)"
    exit 1
}}
'''

print("Running PowerShell script from Python...")
print(f"Script length: {len(ps_script)}")

result = subprocess.run(
    ["powershell", "-Command", ps_script],
    capture_output=True,
    text=True,
    timeout=10
)

print(f"Return code: {result.returncode}")
print(f"Stdout: {result.stdout}")
print(f"Stderr: {result.stderr}")

if result.returncode == 0:
    print("\n[SUCCESS] Notification should appear!")
else:
    print("\n[FAILED] Check errors above")
