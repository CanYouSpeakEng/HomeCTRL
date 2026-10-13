# HomeCTRL - Quick Windows Installer
# Run: powershell -ExecutionPolicy Bypass -File .\install.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "       Installing HomeCTRL (1.0.0)      " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$InstallDir = "$env:LOCALAPPDATA\HomeCTRL"
$ExeSource = "$PSScriptRoot\dist\HomeCTRL.exe"

# Stop existing running instance if any
Stop-Process -Name "HomeCTRL" -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 500

if (-not (Test-Path $ExeSource)) {
    Write-Host "[Error] $ExeSource not found! Please build the executable first using python build_exe.py" -ForegroundColor Red
    exit 1
}

# 1. Create App Directory
Write-Host "[1/4] Setting up installation directory at $InstallDir..." -ForegroundColor Yellow
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}
$AssetsDir = "$InstallDir\assets"
if (-not (Test-Path $AssetsDir)) {
    New-Item -ItemType Directory -Path $AssetsDir -Force | Out-Null
}

# 2. Copy Binaries & Assets
Write-Host "[2/4] Copying files..." -ForegroundColor Yellow
Copy-Item -Path $ExeSource -Destination "$InstallDir\HomeCTRL.exe" -Force
if (Test-Path "$PSScriptRoot\assets") {
    Copy-Item -Path "$PSScriptRoot\assets\*" -Destination $AssetsDir -Recurse -Force
}

# Copy config if present
if (Test-Path "$PSScriptRoot\config.json") {
    Copy-Item -Path "$PSScriptRoot\config.json" -Destination "$InstallDir\config.json" -Force
    Write-Host "      Copied existing config.json to app directory." -ForegroundColor Green
} elseif (Test-Path "$PSScriptRoot\config.example.json") {
    Copy-Item -Path "$PSScriptRoot\config.example.json" -Destination "$InstallDir\config.json" -Force
}

# 3. Create Windows Shortcuts (Start Menu & Desktop)
Write-Host "[3/4] Creating Start Menu & Desktop shortcuts..." -ForegroundColor Yellow
$WshShell = New-Object -ComObject WScript.Shell

# Start Menu Shortcut
$StartMenuDir = [Environment]::GetFolderPath('Programs')
$StartShortcut = $WshShell.CreateShortcut("$StartMenuDir\HomeCTRL.lnk")
$StartShortcut.TargetPath = "$InstallDir\HomeCTRL.exe"
$StartShortcut.WorkingDirectory = $InstallDir
$StartShortcut.IconLocation = "$AssetsDir\app_icon.ico, 0"
$StartShortcut.Description = "HomeCTRL - Smart Lamp & Strip Control"
$StartShortcut.Save()

# Desktop Shortcut
$DesktopDir = [Environment]::GetFolderPath('Desktop')
$DesktopShortcut = $WshShell.CreateShortcut("$DesktopDir\HomeCTRL.lnk")
$DesktopShortcut.TargetPath = "$InstallDir\HomeCTRL.exe"
$DesktopShortcut.WorkingDirectory = $InstallDir
$DesktopShortcut.IconLocation = "$AssetsDir\app_icon.ico, 0"
$DesktopShortcut.Description = "HomeCTRL - Smart Lamp & Strip Control"
$DesktopShortcut.Save()

Write-Host "[4/4] Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "HomeCTRL has been installed to:" -ForegroundColor White
Write-Host "  $InstallDir\HomeCTRL.exe" -ForegroundColor Gray
Write-Host ""
Write-Host "You can now launch HomeCTRL from your Start Menu or Desktop!" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
