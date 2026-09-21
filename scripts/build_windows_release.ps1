$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

python scripts/build_windows_icon.py
python -m PyInstaller --clean --noconfirm SpeedtestMonitorWindows.spec

$InnoCompiler = Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"
if (-not (Test-Path $InnoCompiler)) {
    $InnoCompiler = Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"
}
if (-not (Test-Path $InnoCompiler)) {
    throw "Inno Setup 6 was not found.  Install it, then rerun this script."
}

& $InnoCompiler "installer\windows\SpeedtestMonitor.iss"

$Installer = Join-Path $ProjectRoot "dist\Speedtest-Monitor-Windows-x64-0.2.0.exe"
if (-not (Test-Path $Installer)) {
    throw "The installer was not created: $Installer"
}

Write-Host "Created: $Installer"
