# Test different Windows notification methods

Write-Host "=== Testing Windows Notification Methods ===" -ForegroundColor Cyan
Write-Host ""

# Method 1: Windows.UI.Notifications with explicit loading
Write-Host "Method 1: Windows.UI.Notifications (WinRT)" -ForegroundColor Yellow
try {
    # Try loading with full path
    $assemblyPath = "${env:SystemRoot}\Microsoft.NET\assembly\GAC_MSIL\Windows.UI.Notifications\v4.0_4.0.0.0____Windows.UI.Notifications"
    Write-Host "  Checking assembly path: $assemblyPath"

    # Try alternative loading
    Add-Type -AssemblyName System.Runtime.WindowsRuntime
    Write-Host "  System.Runtime.WindowsRuntime loaded"

    # Load WinRT types
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime] | Out-Null
    Write-Host "  WinRT types loaded successfully"

    $template = @"
    <toast><visual><binding template="ToastText02">
        <text id="1">Test Title</text>
        <text id="2">Test Message</text>
    </binding></visual></toast>
"@

    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml($template)
    $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("ClaudeCode").Show($toast)
    Write-Host "  [SUCCESS] Notification sent!" -ForegroundColor Green
}
catch {
    Write-Host "  [FAILED] $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Method 2: Using shell toast (explorer.exe callback)
Write-Host "Method 2: Shell toast via VBScript" -ForegroundColor Yellow
try {
    $vbsPath = "$env:TEMP\test_notification.vbs"
    @"
    Set objShell = CreateObject("WScript.Shell")
    objShell.Popup "Test notification from VBScript", 5, "Claude Code Test", 64
"@ | Out-File -FilePath $vbsPath -Encoding ASCII
    & cscript.exe //NoLogo $vbsPath
    Remove-Item $vbsPath
    Write-Host "  [SUCCESS] VBScript popup shown!" -ForegroundColor Green
}
catch {
    Write-Host "  [FAILED] $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Method 3: Check if Windows notification center is enabled
Write-Host "Method 3: Check Windows notification settings" -ForegroundColor Yellow
try {
    $registryPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings"
    $enabled = (Get-ItemProperty -Path $registryPath -ErrorAction SilentlyContinue).NOC_GLOBAL_SETTING_ALLOW_NOTIFICATIONS
    if ($enabled -eq 1) {
        Write-Host "  [OK] Notifications are enabled in Windows settings" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] Notifications might be disabled" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "  [INFO] Could not check notification settings" -ForegroundColor Cyan
}
Write-Host ""

Write-Host "=== Test Complete ===" -ForegroundColor Cyan
