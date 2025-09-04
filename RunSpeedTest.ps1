<# =====================================================================
  RunSpeedTest.ps1
  - Starts the collector and Streamlit dashboard in separate PowerShell windows
  - Detects and prefers .\.venv\Scripts\python.exe if present
  - Installs requirements idempotently
  - Seeds Ookla CLI license silently if the speedtest CLI is available
  - Simple, reliable quoting.  No batch parser pitfalls.

  Usage examples:
    .\RunSpeedTest.ps1
    .\RunSpeedTest.ps1 -Interval 120 -Port 8501
    .\RunSpeedTest.ps1 -Headless
    .\RunSpeedTest.ps1 -Python "C:\Python312\python.exe"
===================================================================== #>

[CmdletBinding()]
param(
  [int]$Interval = 120,
  [int]$Port = 8501,
  [switch]$Headless,
  [string]$Python
)

function Resolve-Python {
  param([string]$ExplicitPython)

  # Prefer explicit path if provided and exists
  if ($ExplicitPython) {
    if (Test-Path $ExplicitPython) { return (Resolve-Path $ExplicitPython).Path }
    Write-Warning "Specified Python not found: $ExplicitPython.  Falling back to auto-detect."
  }

  # Prefer local venv if present
  $venvPy = Join-Path -Path (Join-Path -Path $PSScriptRoot -ChildPath ".venv") -ChildPath "Scripts\python.exe"
  if (Test-Path $venvPy) { return (Resolve-Path $venvPy).Path }

  # Otherwise rely on PATH
  $py = Get-Command python -ErrorAction SilentlyContinue
  if ($py) { return $py.Source }

  throw "Python not found.  Install Python or create .\.venv first."
}

function Install-Requirements {
  param([string]$PyExe)

  $req = Join-Path $PSScriptRoot "requirements.txt"
  if (Test-Path $req) {
    Write-Host "Installing/upgrading packages from requirements.txt ..." -ForegroundColor Cyan
    & $PyExe -m pip install --upgrade pip | Out-Host
    & $PyExe -m pip install -r $req | Out-Host
  } else {
    Write-Host "requirements.txt not found.  Skipping dependency install." -ForegroundColor Yellow
  }
}

function Seed-OoklaLicense {
  # If Ookla CLI is present, accept license/GDPR silently once
  $speedtestCmd = Get-Command speedtest -ErrorAction SilentlyContinue
  if ($speedtestCmd) {
    Write-Host "Detected Ookla CLI.  Seeding license acceptance ..." -ForegroundColor Cyan
    try {
      # Suppress output.  Ignore non-zero exit here since some versions exit 1 on first run.
      & $speedtestCmd.Source --accept-license --accept-gdpr -f json --progress=no *> $null
    } catch {
      Write-Host "Note: seeding license returned an error, continuing." -ForegroundColor Yellow
    }
  } else {
    Write-Host "Ookla CLI not found on PATH.  Collector will use Python fallback if configured." -ForegroundColor DarkYellow
  }
}

# --- Main ---

# Always run relative to this script's folder
Set-Location -Path $PSScriptRoot

# Choose Python
$PyExe = Resolve-Python -ExplicitPython $Python
Write-Host "Using Python: $PyExe" -ForegroundColor Green

# Ensure deps
Install-Requirements -PyExe $PyExe

# Seed Ookla license if available
Seed-OoklaLicense

# Build dashboard arguments
$dashArgs = @('-m','streamlit','run','.\dashboard.py','--server.port',"$Port")
if ($Headless.IsPresent) {
  $dashArgs += @('--server.headless','true')
}

# Start Collector in a new PowerShell window that stays open
$collectorCmd = "& '$PyExe' '.\collector.py' --daemon --interval $Interval"
Start-Process -FilePath "powershell.exe" `
  -ArgumentList @('-NoProfile','-NoExit','-Command', $collectorCmd) `
  -WindowStyle Normal `
  -WorkingDirectory $PSScriptRoot `
  -Verb Open `
  -Wait:$false `
  -PassThru | Out-Null

Start-Sleep -Seconds 3

# Start Dashboard in a new PowerShell window that stays open
# Use ArgumentList array to avoid quoting issues
$dashCmd = "& '$PyExe' $($dashArgs | ForEach-Object { "'$_'" } -join ' ')"
Start-Process -FilePath "powershell.exe" `
  -ArgumentList @('-NoProfile','-NoExit','-Command', $dashCmd) `
  -WindowStyle Normal `
  -WorkingDirectory $PSScriptRoot `
  -Verb Open `
  -Wait:$false `
  -PassThru | Out-Null

Write-Host ""
Write-Host "Launched collector (interval $Interval s) and dashboard (http://localhost:$Port)." -ForegroundColor Green
if ($Headless.IsPresent) {
  Write-Host "Dashboard running headless.  Open http://localhost:$Port in your browser." -ForegroundColor Yellow
}
