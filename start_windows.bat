@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title ConvertNest - Local Server

echo ============================================================
echo                 Starting ConvertNest MP3
 echo ============================================================
echo.
where py >nul 2>&1 || goto :python_missing

echo Starting ConvertNest at http://127.0.0.1:5000
echo Close this window to stop the app.
echo.
py app.py
set "EXITCODE=%ERRORLEVEL%"
echo.
echo ConvertNest stopped with exit code %EXITCODE%.
pause
exit /b %EXITCODE%

:python_missing
echo ERROR: Python launcher (py) was not found.
pause
exit /b 1
