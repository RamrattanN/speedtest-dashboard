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

REM --- Pick Python (prefer py -3; fallback to python)
set "PY="

for /f "delims=" %%P in ('where py 2^>nul') do (
  for /f "delims=" %%E in ('%%P -3 -c "import sys;print(sys.executable)" 2^>nul') do (
    set "PY=%%E"
  )
)

if not defined PY (
  for /f "delims=" %%P in ('where python 2^>nul') do (
    set "PY=%%P"
    goto :have_python
  )
)

:have_python
if not defined PY (
  echo [ERROR] Python not found on PATH. Install Python 3.10+ and try again.
  goto :end
)

echo [INFO] Python: "%PY%"

REM --- Install/upgrade requirements (harmless if already satisfied)
if exist "%ROOT%requirements.txt" (
  echo [INFO] Installing/upgrading Python packages from requirements.txt ...
  "%PY%" -m pip install -r "%ROOT%requirements.txt"
  if errorlevel 1 (
    echo [WARN] pip install returned a non-zero exit code. Continuing...
  )
) else (
  echo [INFO] No requirements.txt found. Skipping dependency install.
)

REM --- If Ookla CLI is present, seed license acceptance so collector can use it
if exist "%ROOT%speedtest.exe" (
  echo [INFO] Detected Ookla CLI. Seeding license acceptance ...
  "%ROOT%speedtest.exe" --accept-license --accept-gdpr >nul 2>nul
)

REM --- Interval in seconds (first arg), default 120
set "INTERVAL=%~1"
if not defined INTERVAL set "INTERVAL=120"
echo [INFO] Collector interval: %INTERVAL% seconds

REM --- Launch collector (window stays open)
start "Speedtest Collector" powershell -NoExit -ExecutionPolicy Bypass ^
  -Command "Set-Location -LiteralPath '%ROOT%'; & '%PY%' 'collector.py' --daemon --interval %INTERVAL%"

REM --- Launch dashboard (window stays open)
start "Speedtest Dashboard" powershell -NoExit -ExecutionPolicy Bypass ^
  -Command "Set-Location -LiteralPath '%ROOT%'; & '%PY%' -m streamlit run 'dashboard.py'"

echo.
echo [INFO] Launched collector and dashboard.
echo [INFO] Dashboard URL: http://localhost:8501
echo.

:end
popd
endlocal
