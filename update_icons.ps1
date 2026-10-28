
$WshShell = New-Object -ComObject WScript.Shell
$WorkDir = $PSScriptRoot
if (-not $WorkDir) { $WorkDir = "D:\REPO GITHUB\Presentasi" }
$IconPath = Join-Path $WorkDir "app_icon.ico"
$TargetScript = Join-Path $WorkDir "teleprompter_overlay.py"

$Pythonw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $Pythonw) { $Pythonw = "C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\pythonw.exe" }

$StartMenuDir = [System.Environment]::GetFolderPath('Programs')
$DesktopDir = [System.Environment]::GetFolderPath('Desktop')

# Clean old shortcuts
$OldStartLnk = Join-Path $StartMenuDir "KPPM Teleprompter.lnk"
$OldDesktopLnk = Join-Path $DesktopDir "KPPM Teleprompter.lnk"
if (Test-Path $OldStartLnk) { Remove-Item -Path $OldStartLnk -Force }
if (Test-Path $OldDesktopLnk) { Remove-Item -Path $OldDesktopLnk -Force }

# 1. Start Menu Shortcut
$StartLnk = Join-Path $StartMenuDir "Teleprompter by tourrr.lnk"
$Shortcut1 = $WshShell.CreateShortcut($StartLnk)
$Shortcut1.TargetPath = $Pythonw
$Shortcut1.Arguments = "`"$TargetScript`""
$Shortcut1.WorkingDirectory = $WorkDir
$Shortcut1.Description = "Teleprompter by tourrr - Floating Overlay"
$Shortcut1.IconLocation = "$IconPath,0"
$Shortcut1.Save()

# 2. Desktop Shortcut
$DesktopLnk = Join-Path $DesktopDir "Teleprompter by tourrr.lnk"
$Shortcut2 = $WshShell.CreateShortcut($DesktopLnk)
$Shortcut2.TargetPath = $Pythonw
$Shortcut2.Arguments = "`"$TargetScript`""
$Shortcut2.WorkingDirectory = $WorkDir
$Shortcut2.Description = "Teleprompter by tourrr - Floating Overlay"
$Shortcut2.IconLocation = "$IconPath,0"
$Shortcut2.Save()

Write-Output "Shortcuts updated with custom app icon successfully!"
