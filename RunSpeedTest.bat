@echo off
setlocal ENABLEDELAYEDEXPANSION

rem -----------------------------------------------------------------------------
rem  Speedtest Dashboard launcher (Windows)
rem  - Uses local venv if present (.\.venv).  Otherwise uses system Python.
rem  - Ensures requirements are installed.
rem  - Seeds Ookla CLI license if the 'speedtest' binary is on PATH.
rem  - Starts Collector and Dashboard in separate windows.
rem -----------------------------------------------------------------------------

rem === Settings you may change ===
set INTERVAL=120
set DASHBOARD_PORT=8501
set OPEN_BROWSER=1
rem ================================

rem Move to the folder where this .bat resides
cd /d "%~dp0"

rem Prefer a local virtual environment if it exists
set PY_EXE=python
if exist ".venv\Scripts\python.exe" (
  set PY_EXE=.venv\Scripts\python.exe
)

rem Show which Python will be used
echo Using Python: %PY_EXE%
echo.

rem Install requirements (safe to run repeatedly)
if exist "requirements.txt" (
  echo Installing/upgrading Python packages from requirements.txt ...
  "%PY_EXE%" -m pip install --upgrade pip >nul
  "%PY_EXE%" -m pip install -r requirements.txt
  echo.
)

rem If Ookla CLI is installed, seed license acceptance once (no output)
where speedtest >nul 2>&1
if %ERRORLEVEL%==0 (
  echo Detected Ookla CLI.  Seeding license acceptance (once) ...
  speedtest --accept-license --accept-gdpr -f json --progress=no >nul 2>&1
  echo.
)

rem Start the collector (daemon).  Uses our resilient collector.py.
echo Starting collector (interval %INTERVAL%s) ...
start "Collector" cmd /k "%PY_EXE% collector.py --daemon --interval %INTERVAL%"

rem Give the collector a brief head start
timeout /t 3 >nul

rem Start the Streamlit dashboard
echo Starting dashboard on http://localhost:%DASHBOARD_PORT% ...
set STREAMLIT_CMD=%PY_EXE% -m streamlit run dashboard.py --server.port %DASHBOARD_PORT% --server.headless true
if "%OPEN_BROWSER%"=="1" (
  rem Let Streamlit open the browser automatically
) else (
  set STREAMLIT_CMD=%STREAMLIT_CMD% --server.headless true
)

start "Dashboard" cmd /k %STREAMLIT_CMD%

echo.
echo Done.  Two windows should be open:  "Collector" and "Dashboard".
echo If a browser did not open, visit:  http://localhost:%DASHBOARD_PORT%
echo.

endlocal
