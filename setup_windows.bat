@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

title ConvertNest - Windows Setup

echo ============================================================
echo                 ConvertNest Windows Setup
echo ============================================================
echo.

echo [1/5] Checking Python...
where py >nul 2>&1
if errorlevel 1 goto :python_missing
py --version

echo.
echo [2/5] Checking Git...
where git >nul 2>&1
if errorlevel 1 goto :git_missing
git --version

echo.
echo [3/5] Checking Node.js...
where node >nul 2>&1
if errorlevel 1 goto :node_missing
for /f "delims=" %%V in ('node -p "process.versions.node"') do set NODEVER=%%V
for /f "tokens=1 delims=." %%M in ("!NODEVER!") do set NODEMAJOR=%%M
node --version
if !NODEMAJOR! LSS 22 goto :node_old

echo.
echo [4/5] Installing Python packages...
py -m pip install --upgrade pip
if errorlevel 1 goto :pip_failed
py -m pip install -r requirements.txt
if errorlevel 1 goto :pip_failed

echo.
echo [5/5] Preparing bgutil PO-token provider...
echo If npm shows a deprecated-package WARNING, that is not a failure.
echo This setup window will remain open until setup is completely finished.
if exist "vendor\bgutil-ytdlp-pot-provider\server\build\main.js" goto :provider_ready
if not exist "vendor" mkdir vendor
if exist "vendor\bgutil-ytdlp-pot-provider" rmdir /s /q "vendor\bgutil-ytdlp-pot-provider"
git clone --depth 1 --branch 1.3.2 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git "vendor\bgutil-ytdlp-pot-provider"
if errorlevel 1 goto :git_clone_failed
pushd "vendor\bgutil-ytdlp-pot-provider\server"
call npm ci --no-audit --no-fund
if errorlevel 1 (popd & goto :npm_failed)
call npx tsc
if errorlevel 1 (popd & goto :npm_failed)
popd

:provider_ready
echo.
echo ============================================================
echo SETUP COMPLETE
echo ============================================================
echo.
echo Start the app with:
echo     start_windows.bat
echo.
echo This window will stay open if there is an error.
echo.
pause
exit /b 0

:python_missing
call :fail "Python launcher (py) was not found. Install Python 3.11+ and enable the Python Launcher."
exit /b 1
:git_missing
call :fail "Git was not found. Install Git for Windows."
exit /b 1
:node_missing
call :fail "Node.js was not found. Install Node.js 22+ and run setup again."
exit /b 1
:node_old
call :fail "Node.js !NODEVER! is too old. ConvertNest requires Node.js 22+ for current yt-dlp YouTube challenge solving."
exit /b 1
:pip_failed
call :fail "Python dependency installation failed. Read the error above."
exit /b 1
:git_clone_failed
call :fail "Could not download the bgutil provider from GitHub. Check your internet connection and Git installation."
exit /b 1
:npm_failed
call :fail "Node/npm provider build failed. Read the npm error above."
exit /b 1

:fail
echo.
echo ============================================================
echo ERROR
echo %~1
echo ============================================================
echo.
pause
exit /b 1
