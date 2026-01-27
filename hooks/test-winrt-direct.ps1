# Direct test of WinRT method
$title = "Test Title"
$message = "Test Message"

$title_escaped = $title -replace "'", "''"
$message_escaped = $message -replace "'", "''"

try {
    Add-Type -AssemblyName System.Runtime.WindowsRuntime -ErrorAction Stop
    Write-Host "System.Runtime.WindowsRuntime loaded"

    $null = [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
    Write-Host "ToastNotificationManager type loaded"

    $null = [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime]
    Write-Host "XmlDocument type loaded"

    $template = @"
    <toast><visual><binding template="ToastText02">
        <text id="1">$title_escaped</text>
        <text id="2">$message_escaped</text>
    </binding></visual></toast>
"@

    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml($template)
    Write-Host "XML loaded"

    $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
    Write-Host "Toast created"

    $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("ClaudeCode")
    Write-Host "Notifier created"

    $notifier.Show($toast)
    Write-Host "Notification sent!"
    exit 0
} catch {
    Write-Host "ERROR: $($_.Exception.Message)"
    Write-Host "Stack: $($_.ScriptStackTrace)"
    exit 1
}
