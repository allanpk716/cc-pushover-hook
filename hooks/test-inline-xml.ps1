# Test inline XML method
$title = "Test Title"
$message = "Test Message with newline`nand more"

$title_escaped = $title -replace "'", "''"
$message_escaped = $message -replace "'", "''"

Write-Host "Title: $title_escaped"
Write-Host "Message: $message_escaped"

try {
    Add-Type -AssemblyName System.Runtime.WindowsRuntime -ErrorAction Stop
    Write-Host "Runtime loaded"

    $null = [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
    $null = [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime]
    Write-Host "Types loaded"

    $xmlString = "<toast><visual><binding template=`"ToastText02`"><text id=`"1`">$title_escaped</text><text id=`"2`">$message_escaped</text></binding></visual></toast>"
    Write-Host "XML string created"

    $xmlDoc = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xmlDoc.LoadXml($xmlString)
    Write-Host "XML document created"

    $toast = New-Object Windows.UI.Notifications.ToastNotification $xmlDoc
    Write-Host "Toast created"

    $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("ClaudeCode")
    $notifier.Show($toast)
    Write-Host "SUCCESS!"
    exit 0
} catch {
    Write-Host "ERROR: $($_.Exception.Message)"
    Write-Host "Stack: $($_.ScriptStackTrace)"
    exit 1
}
