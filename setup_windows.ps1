$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
Write-Host '=== ConvertNest local YouTube setup ==='

if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw 'Python launcher not found. Install Python 3.11+ first.' }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git not found. Install Git for Windows, then run this again.' }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw 'Node.js 22+ not found. Install Node.js 22+ and run this again.' }

$nodeVersion = node -p "process.versions.node"
$major = [int]($nodeVersion.Split('.')[0])
if ($major -lt 22) { throw "Node.js $nodeVersion found. ConvertNest requires Node.js 22+ for current yt-dlp EJS." }

py -m pip install --upgrade pip
py -m pip install -r requirements.txt

$main = Join-Path $PSScriptRoot 'vendor\bgutil-ytdlp-pot-provider\server\build\main.js'
if (-not (Test-Path $main)) {
    New-Item -ItemType Directory -Force -Path (Join-Path $PSScriptRoot 'vendor') | Out-Null
    git clone --depth 1 --branch 1.3.2 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git (Join-Path $PSScriptRoot 'vendor\bgutil-ytdlp-pot-provider')
    Push-Location (Join-Path $PSScriptRoot 'vendor\bgutil-ytdlp-pot-provider\server')
    npm ci
    npx tsc
    Pop-Location
}

Write-Host ''
Write-Host 'Setup complete. Start ConvertNest with: py app.py'
