@echo off
setlocal ENABLEDELAYEDEXPANSION

rem -----------------------------------------------------------------------------
rem  setup_venv.bat
rem  Creates a local Python virtual environment at .\.venv and installs deps.
rem  Works with either the 'py' launcher or 'python' on PATH.
rem -----------------------------------------------------------------------------

rem Move to this script's directory
cd /d "%~dp0"

echo.
echo === Detecting Python ===
set PY_EXE=
where py >nul 2>&1
if %ERRORLEVEL%==0 (
  for /f "delims=" %%I in ('py -c "import sys;print(sys.executable)"') do set "PY_EXE=%%I"
) else (
  where python >nul 2>&1
  if %ERRORLEVEL%==0 (
    for /f "delims=" %%I in ('python -c "import sys;print(sys.executable)"') do set "PY_EXE=%%I"
  )
)

if "%PY_EXE%"=="" (
  echo ERROR: No Python found on PATH.  Install Python 3.11+ and re-run.
  exit /b 1
)

echo Using Python: %PY_EXE%

echo.
echo === Creating virtual environment at .venv ===
"%PY_EXE%" -m venv .venv
if %ERRORLEVEL% NEQ 0 (
  echo ERROR: Failed to create virtual environment.
  exit /b 1
)

echo.
echo === Upgrading pip and installing requirements ===
".venv\Scripts\python.exe" -m pip install --upgrade pip
if exist "requirements.txt" (
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
) else (
  echo WARNING: requirements.txt not found.  Skipping dependency install.
)

echo.
echo === Verifying Streamlit and core packages ===
".venv\Scripts\python.exe" -c "import sys;print('Python:',sys.version)"
".venv\Scripts\python.exe" -c "import streamlit, pandas; print('OK: streamlit', streamlit.__version__, 'pandas', pandas.__version__)" 2>NUL

echo.
echo Done.  A local venv is ready at .venv  and RunSpeedTest.bat will use it automatically.
echo To start everything now run:  RunSpeedTest.bat
echo.

endlocal
