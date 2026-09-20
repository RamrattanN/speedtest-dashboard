# RunSpeedTest.ps1
# Launches the collector and Streamlit dashboard in separate PowerShell windows.
param(
  [int]$Interval = 120,
  [int]$Port = 8501,
  [switch]$Headless,
  [string]$DataDir = "$HOME\SpeedtestDashboard"
)

$ErrorActionPreference = 'Stop'

# --- Project root is the folder this script lives in
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
Write-Host "Project root: $Root"

# --- Choose shell for child windows (pwsh preferred)
$PwshCommand = Get-Command pwsh -ErrorAction SilentlyContinue
if ($PwshCommand) {
  $Shell = $PwshCommand.Source
} else {
  $Shell = (Get-Command powershell -ErrorAction Stop).Source
}

# --- Create and use a project-local Python environment
$VenvPython = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path $VenvPython)) {
  $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
  if (-not $PythonCommand) { throw "Python not found on PATH." }
  $SystemPython = $PythonCommand.Source
  & $SystemPython -m venv (Join-Path $Root '.venv')
}
$Py = $VenvPython
& $Py -m pip install -e $Root

# --- Optional: pre-accept Ookla CLI license if speedtest.exe is present
$OoklaExe = Join-Path $Root 'speedtest.exe'
if (Test-Path $OoklaExe) {
  try {
    Write-Host "Detected Ookla CLI. Seeding license acceptance ..."
    & $OoklaExe --accept-license --accept-gdpr | Out-Null
  } catch { Write-Host "  (skip) $($_.Exception.Message)" }
}

$CollectorArgs = @(
  '-NoExit','-Command', "Set-Location '$Root'; & '$Py' -m speedtest_dashboard.collector_app --daemon --interval $Interval --data-dir '$DataDir'"
)

$DashboardCommand = "Set-Location '$Root'; `$env:SPEEDTEST_DASHBOARD_DATA_DIR='$DataDir'; & '$Py' -m streamlit run 'dashboard.py' --server.port $Port"
if ($Headless) { $DashboardCommand += " --server.headless true --browser.gatherUsageStats false" }
$DashboardArgs = @(
  '-NoExit','-Command', $DashboardCommand
)

# --- Launch two windows
$col = Start-Process -FilePath $Shell -ArgumentList $CollectorArgs -WindowStyle Normal -PassThru -Verb Open
$db  = Start-Process -FilePath $Shell -ArgumentList $DashboardArgs -WindowStyle Normal -PassThru -Verb Open

Write-Host "Launched collector (PID $($col.Id)) and dashboard (PID $($db.Id))."
Write-Host "Dashboard will be at http://localhost:$Port"
Write-Host "Results will be saved in $DataDir"
