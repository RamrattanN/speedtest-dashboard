# RunSpeedTest.ps1
# Launches the collector and Streamlit dashboard in separate PowerShell windows.
# Assumes this script lives in the project root:
# C:\Users\niles\Dropbox\Python Code\Speedtest\

$ErrorActionPreference = 'Stop'

# --- Project root is the folder this script lives in
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
Write-Host "Project root: $Root"

# --- Choose shell for child windows (pwsh preferred)
$Shell = (Get-Command pwsh -ErrorAction SilentlyContinue)?.Source
if (-not $Shell) { $Shell = (Get-Command powershell -ErrorAction Stop).Source }

# --- Choose Python
$Py = (Get-Command python -ErrorAction SilentlyContinue)?.Source
if (-not $Py) { throw "Python not found on PATH." }

# --- Optional: make sure deps are installed
$Req = Join-Path $Root 'requirements.txt'
if (Test-Path $Req) {
  Write-Host "Installing/upgrading Python packages from requirements.txt ..."
  & $Py -m pip install -r $Req
}

# --- Optional: pre-accept Ookla CLI license if speedtest.exe is present
$OoklaExe = Join-Path $Root 'speedtest.exe'
if (Test-Path $OoklaExe) {
  try {
    Write-Host "Detected Ookla CLI. Seeding license acceptance ..."
    & $OoklaExe --accept-license --accept-gdpr | Out-Null
  } catch { Write-Host "  (skip) $($_.Exception.Message)" }
}

# --- Arguments (interval is easy to tweak)
$IntervalSec = 120

$CollectorArgs = @(
  '-NoExit','-Command', "Set-Location '$Root'; & '$Py' 'collector.py' --daemon --interval $IntervalSec"
)

$DashboardArgs = @(
  '-NoExit','-Command', "Set-Location '$Root'; & '$Py' -m streamlit run 'dashboard.py'"
)

# --- Launch two windows
$col = Start-Process -FilePath $Shell -ArgumentList $CollectorArgs -WindowStyle Normal -PassThru -Verb Open
$db  = Start-Process -FilePath $Shell -ArgumentList $DashboardArgs -WindowStyle Normal -PassThru -Verb Open

Write-Host "Launched collector (PID $($col.Id)) and dashboard (PID $($db.Id))."
Write-Host "Dashboard will be at http://localhost:8501"
