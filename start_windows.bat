@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title ConvertNest - Local Server

echo ============================================================
echo                 Starting ConvertNest
echo ============================================================
echo.
where py >nul 2>&1 || goto :python_missing
where node >nul 2>&1 || goto :node_missing
if not exist "vendor\bgutil-ytdlp-pot-provider\server\build\main.js" goto :setup_missing

set "YTDL_POT_PROVIDER_URL=http://127.0.0.1:4416"

echo Starting YouTube PO-token provider...
start "ConvertNest PO Provider" /min cmd /c "cd /d ""%~dp0vendor\bgutil-ytdlp-pot-provider\server"" && node build\main.js --port 4416 > ""%TEMP%\convertnest-bgutil.log"" 2>&1"

set /a tries=0
:wait
set /a tries+=1
powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing http://127.0.0.1:4416/ping -TimeoutSec 1 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 goto :provider_ready
if %tries% GEQ 30 goto :provider_failed
timeout /t 1 /nobreak >nul
goto :wait

:provider_ready
echo PO-token provider is ready.
echo.
echo Starting ConvertNest at http://127.0.0.1:5000
echo Close this window to stop the app.
echo.
py app.py
set "EXITCODE=%ERRORLEVEL%"
echo.
echo ConvertNest stopped with exit code %EXITCODE%.
echo If it stopped unexpectedly, copy the error shown above and send it to me.
pause
exit /b %EXITCODE%

:provider_failed
echo.
echo ERROR: PO-token provider did not start.
echo Check %TEMP%\convertnest-bgutil.log
pause
exit /b 1
:setup_missing
echo ERROR: Setup has not completed. Run setup_windows.bat first.
pause
exit /b 1
:python_missing
echo ERROR: Python launcher (py) was not found.
pause
exit /b 1
:node_missing
echo ERROR: Node.js was not found.
pause
exit /b 1
