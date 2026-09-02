@echo off
setlocal EnableExtensions
cd /d "%~dp0"

title ConvertNest - Windows Setup

echo ============================================================
echo              ConvertNest MP3 Windows Setup
echo ============================================================
echo.

where py >nul 2>&1 || goto :python_missing
py --version

echo.
echo Installing Python packages...
py -m pip install --upgrade pip
if errorlevel 1 goto :pip_failed
py -m pip install -r requirements.txt
if errorlevel 1 goto :pip_failed

echo.
echo SETUP COMPLETE
echo Start the app with: start_windows.bat
echo.
pause
exit /b 0

:python_missing
echo ERROR: Python launcher (py) was not found. Install Python 3.11+.
pause
exit /b 1
:pip_failed
echo ERROR: Python dependency installation failed. Read the error above.
pause
exit /b 1
