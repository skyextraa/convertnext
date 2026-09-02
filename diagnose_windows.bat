@echo off
cd /d "%~dp0"
title ConvertNest - Diagnostics

echo === ConvertNest diagnostics ===
echo Folder: %CD%
echo.
py --version 2>&1
node --version 2>&1
npm --version 2>&1
ffmpeg -version 2>&1 | findstr /B /C:"ffmpeg version"
echo.
echo === yt-dlp ===
py -m yt_dlp --version 2>&1
echo.
echo === bgutil provider ===
if exist "vendor\bgutil-ytdlp-pot-provider\server\build\main.js" (echo Provider build: OK) else (echo Provider build: MISSING)
py -m yt_dlp -v --extractor-args "youtube:player_client=mweb;fetch_pot=always;formats=missing_pot" "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
echo.
echo Diagnostics finished. This window will stay open.
pause
