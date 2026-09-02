@echo off
setlocal
cd /d "%~dp0"
echo === Python ===
py --version
echo === Dependencies ===
py -m pip show yt-dlp Flask imageio-ffmpeg
echo === ConvertNest files ===
dir /b
pause
