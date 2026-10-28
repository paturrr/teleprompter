import os
from PIL import Image, ImageDraw, ImageFont
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ICO_PATH = os.path.join(SCRIPT_DIR, "app_icon.ico")
PNG_PATH = os.path.join(SCRIPT_DIR, "app_icon.png")

def create_app_icon():
    # 256x256 high-res canvas
    size = 256
    img = Image.new("RGBA", (size, size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Background Rounded Circle / Squircle (Glassmorphism Emerald gradient)
    pad = 12
    draw.rounded_rectangle(
        (pad, pad, size - pad, size - pad),
        radius=54,
        fill="#047857",
        outline="#10b981",
        width=8
    )

    # 2. Inner floating document/prompter screen
    doc_pad_x = 58
    doc_pad_y = 48
    draw.rounded_rectangle(
        (doc_pad_x, doc_pad_y, size - doc_pad_x, size - doc_pad_y),
        radius=20,
        fill="#0b131e",
        outline="#34d399",
        width=6
    )

    # 3. Teleprompter / Screen Play symbol & Text lines
    # Play indicator in emerald
    # Text lines on prompter screen
    line_x1 = 80
    line_x2 = 176
    draw.rounded_rectangle((line_x1, 78, line_x2, 88), radius=5, fill="#10b981")
    draw.rounded_rectangle((line_x1, 102, line_x2, 112), radius=5, fill="#f8fafc")
    draw.rounded_rectangle((line_x1, 126, line_x2 - 24, 136), radius=5, fill="#f8fafc")
    draw.rounded_rectangle((line_x1, 150, line_x2, 160), radius=5, fill="#94a3b8")
    
    # 4. Microphone / Voice dot indicator at bottom right of screen
    draw.ellipse((152, 168, 172, 188), fill="#10b981", outline="#6ee7b7", width=2)

    # Save PNG
    img.save(PNG_PATH, "PNG")

    # Save Multi-resolution ICO
    icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(ICO_PATH, format="ICO", sizes=icon_sizes)
    print(f"Generated Icon: {ICO_PATH}")

def update_shortcuts_with_icon():
    import sys, shutil
    python_dir = os.path.dirname(sys.executable)
    pythonw_path = os.path.join(python_dir, "pythonw.exe")
    if not os.path.exists(pythonw_path):
        which_pythonw = shutil.which("pythonw")
        pythonw_path = which_pythonw if which_pythonw else sys.executable

    target_script = os.path.join(SCRIPT_DIR, "teleprompter_overlay.py")
    ps_content = f'''
$WshShell = New-Object -ComObject WScript.Shell
$WorkDir = $PSScriptRoot
if (-not $WorkDir) {{ $WorkDir = "{SCRIPT_DIR}" }}
$IconPath = Join-Path $WorkDir "app_icon.ico"
$TargetScript = Join-Path $WorkDir "teleprompter_overlay.py"

$Pythonw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $Pythonw) {{ $Pythonw = "{pythonw_path}" }}

$StartMenuDir = [System.Environment]::GetFolderPath('Programs')
$DesktopDir = [System.Environment]::GetFolderPath('Desktop')

# Clean old shortcuts
$OldStartLnk = Join-Path $StartMenuDir "KPPM Teleprompter.lnk"
$OldDesktopLnk = Join-Path $DesktopDir "KPPM Teleprompter.lnk"
if (Test-Path $OldStartLnk) {{ Remove-Item -Path $OldStartLnk -Force }}
if (Test-Path $OldDesktopLnk) {{ Remove-Item -Path $OldDesktopLnk -Force }}

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
'''
    ps_path = os.path.join(SCRIPT_DIR, "update_icons.ps1")
    with open(ps_path, "w", encoding="utf-8") as f:
        f.write(ps_content)

    res = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_path], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr)

if __name__ == "__main__":
    create_app_icon()
    update_shortcuts_with_icon()
