@echo off
setlocal enableextensions enabledelayedexpansion
REM ------------------------------------------------------------
REM RunSpeedTest.bat  (standalone launcher)
REM   - Installs deps (if requirements.txt exists)
REM   - (Optionally) accepts Ookla CLI license if speedtest.exe found
REM   - Launches collector and dashboard in separate PowerShell windows
REM ------------------------------------------------------------

REM --- Project root = folder this BAT lives in
set "ROOT=%~dp0"
pushd "%ROOT%"

echo.
echo [INFO] Project root: "%ROOT%"

REM --- Use a project-local virtual environment
set "PY=%ROOT%.venv\Scripts\python.exe"

if not exist "%PY%" (
  where py >nul 2>nul
  if not errorlevel 1 (
    py -3 -m venv "%ROOT%.venv"
  ) else (
    where python >nul 2>nul
    if errorlevel 1 (
      echo [ERROR] Python not found on PATH. Install Python 3.11+ and try again.
      goto :end
    )
    python -m venv "%ROOT%.venv"
  )
)

echo [INFO] Python: "%PY%"

echo [INFO] Installing/updating Speedtest Dashboard ...
"%PY%" -m pip install -e "%ROOT%"
if errorlevel 1 goto :end

REM --- If Ookla CLI is present, seed license acceptance so collector can use it
if exist "%ROOT%speedtest.exe" (
  echo [INFO] Detected Ookla CLI. Seeding license acceptance ...
  "%ROOT%speedtest.exe" --accept-license --accept-gdpr >nul 2>nul
)

REM --- Interval in seconds (first arg), default 120
set "INTERVAL=%~1"
if not defined INTERVAL set "INTERVAL=120"
set "PORT=%~2"
if not defined PORT set "PORT=8501"
set "DATA_DIR=%USERPROFILE%\SpeedtestDashboard"
echo [INFO] Collector interval: %INTERVAL% seconds

REM --- Launch collector (window stays open)
start "Speedtest Collector" powershell -NoExit -ExecutionPolicy Bypass ^
  -Command "Set-Location -LiteralPath '%ROOT%'; & '%PY%' -m speedtest_dashboard.collector_app --daemon --interval %INTERVAL% --data-dir '%DATA_DIR%'"

REM --- Launch dashboard (window stays open)
start "Speedtest Dashboard" powershell -NoExit -ExecutionPolicy Bypass ^
  -Command "Set-Location -LiteralPath '%ROOT%'; $env:SPEEDTEST_DASHBOARD_DATA_DIR='%DATA_DIR%'; & '%PY%' -m streamlit run 'dashboard.py' --server.port %PORT%"

echo.
echo [INFO] Launched collector and dashboard.
echo [INFO] Dashboard URL: http://localhost:%PORT%
echo [INFO] Results folder: %DATA_DIR%
echo.

:end
popd
endlocal
