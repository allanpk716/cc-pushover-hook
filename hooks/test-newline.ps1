# Test with actual newlines in heredoc
$title = "Test Title"
$message = "Line 1`nLine 2"

$title_escaped = $title -replace "'", "''"
$message_escaped = $message -replace "'", "''"

Write-Host "Testing with newline in message..."

try {
    Add-Type -AssemblyName System.Runtime.WindowsRuntime -ErrorAction Stop
    $null = [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
    $null = [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime]

    # Using actual newline in heredoc
    $template = @"
<toast><visual><binding template="ToastText02">
    <text id="1">$title_escaped</text>
    <text id="2">$message_escaped</text>
</binding></visual></toast>
"@

    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml($template)
    $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("ClaudeCode").Show($toast)
    Write-Host "SUCCESS!"
    exit 0
} catch {
    Write-Host "ERROR: $($_.Exception.Message)"
    Write-Host "Type: $($_.Exception.GetType().FullName)"
    exit 1
}
