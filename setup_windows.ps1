$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
Write-Host '=== ConvertNest MP3 local setup ==='
if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw 'Python launcher not found. Install Python 3.11+ first.' }
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
Write-Host 'Setup complete. Start ConvertNest with: .\start_windows.bat'
