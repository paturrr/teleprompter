import os
import sys
import shutil
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ICO_PATH = os.path.join(SCRIPT_DIR, "app_icon.ico")
SCRIPT_PY = os.path.join(SCRIPT_DIR, "teleprompter_overlay.py")

# Detect pythonw.exe path dynamically
python_dir = os.path.dirname(sys.executable)
pythonw_path = os.path.join(python_dir, "pythonw.exe")
if not os.path.exists(pythonw_path):
    which_pythonw = shutil.which("pythonw")
    pythonw_path = which_pythonw if which_pythonw else sys.executable

ps_content = f'''
$WshShell = New-Object -ComObject WScript.Shell
$WorkDir = $PSScriptRoot
if (-not $WorkDir) {{ $WorkDir = "{SCRIPT_DIR}" }}
$IconPath = Join-Path $WorkDir "app_icon.ico"
$TargetScript = Join-Path $WorkDir "teleprompter_overlay.py"

$Pythonw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $Pythonw) {{ $Pythonw = "{pythonw_path}" }}

# 1. Clean up obsolete shortcuts
$StartMenuDir = [System.Environment]::GetFolderPath('Programs')
$DesktopDir = [System.Environment]::GetFolderPath('Desktop')

$OldStartLnk = Join-Path $StartMenuDir "KPPM Teleprompter.lnk"
$OldDesktopLnk = Join-Path $DesktopDir "KPPM Teleprompter.lnk"
if (Test-Path $OldStartLnk) {{ Remove-Item -Path $OldStartLnk -Force; Write-Output "Removed old shortcut: $OldStartLnk" }}
if (Test-Path $OldDesktopLnk) {{ Remove-Item -Path $OldDesktopLnk -Force; Write-Output "Removed old shortcut: $OldDesktopLnk" }}

# 2. Start Menu Shortcut
$StartLnk = Join-Path $StartMenuDir "Teleprompter by tourrr.lnk"
$Shortcut1 = $WshShell.CreateShortcut($StartLnk)
$Shortcut1.TargetPath = $Pythonw
$Shortcut1.Arguments = "`"$TargetScript`""
$Shortcut1.WorkingDirectory = $WorkDir
$Shortcut1.Description = "Teleprompter by tourrr - Floating Overlay"
if (Test-Path $IconPath) {{ $Shortcut1.IconLocation = "$IconPath,0" }}
$Shortcut1.Save()
Write-Output "Start Menu Shortcut: $StartLnk"

# 3. Desktop Shortcut
$DesktopLnk = Join-Path $DesktopDir "Teleprompter by tourrr.lnk"
$Shortcut2 = $WshShell.CreateShortcut($DesktopLnk)
$Shortcut2.TargetPath = $Pythonw
$Shortcut2.Arguments = "`"$TargetScript`""
$Shortcut2.WorkingDirectory = $WorkDir
$Shortcut2.Description = "Teleprompter by tourrr - Floating Overlay"
if (Test-Path $IconPath) {{ $Shortcut2.IconLocation = "$IconPath,0" }}
$Shortcut2.Save()
Write-Output "Desktop Shortcut: $DesktopLnk"
'''

ps_file = os.path.join(SCRIPT_DIR, "create_shortcuts.ps1")
with open(ps_file, "w", encoding="utf-8") as f:
    f.write(ps_content.strip() + "\n")

res = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_file], capture_output=True, text=True)
print(res.stdout)
if res.stderr:
    print(res.stderr)
