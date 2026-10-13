# HomeCTRL - Windows Uninstaller
# Run: powershell -ExecutionPolicy Bypass -File .\uninstall.ps1

Write-Host "Uninstalling HomeCTRL..." -ForegroundColor Yellow

# Kill running instance if any
Stop-Process -Name "HomeCTRL" -ErrorAction SilentlyContinue

# Remove shortcuts
$StartMenuDir = [Environment]::GetFolderPath('Programs')
$DesktopDir = [Environment]::GetFolderPath('Desktop')
Remove-Item -Path "$StartMenuDir\HomeCTRL.lnk" -ErrorAction SilentlyContinue
Remove-Item -Path "$DesktopDir\HomeCTRL.lnk" -ErrorAction SilentlyContinue

# Remove startup entry
Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "HomeCTRL" -ErrorAction SilentlyContinue

# Remove folder
$InstallDir = "$env:LOCALAPPDATA\HomeCTRL"
if (Test-Path $InstallDir) {
    Remove-Item -Path $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "HomeCTRL successfully uninstalled." -ForegroundColor Green
