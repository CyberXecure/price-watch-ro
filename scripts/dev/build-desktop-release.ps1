$ErrorActionPreference = "Stop"

$ProjectRoot = "D:\dev\projects\price-watch-ro"
$ApiDir = Join-Path $ProjectRoot "services\api"
$WebDir = Join-Path $ProjectRoot "apps\web"
$TauriDir = Join-Path $ProjectRoot "desktop\src-tauri"
$ApiDistDir = Join-Path $ProjectRoot "build\api-dist"
$WebExportDir = Join-Path $ProjectRoot "build\web-export"

Write-Host "=== BUILD API SIDECAR ==="

if (Test-Path $ApiDistDir) {
    Remove-Item $ApiDistDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $ApiDistDir | Out-Null

Set-Location $ApiDir
.\.venv\Scripts\python.exe -m PyInstaller .\price-watch-api.spec --noconfirm

$apiBuiltExe = Join-Path $ApiDir "dist\price-watch-api.exe"
if (-not (Test-Path $apiBuiltExe)) {
    throw "Nu am găsit $apiBuiltExe după PyInstaller."
}

Copy-Item $apiBuiltExe (Join-Path $ApiDistDir "price-watch-api-x86_64-pc-windows-msvc.exe") -Force

Write-Host ""
Write-Host "=== BUILD WEB ==="

$env:NEXT_PUBLIC_API_BASE = "http://127.0.0.1:18400"
$env:NEXT_PUBLIC_APP_MODE = "desktop"
$env:BUILD_DESKTOP = "1"

Set-Location $WebDir
npm run build

Set-Location $ProjectRoot

if (Test-Path $WebExportDir) {
    Remove-Item $WebExportDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $WebExportDir | Out-Null

$webOutDir = Join-Path $WebDir "out"
if (Test-Path $webOutDir) {
    Copy-Item (Join-Path $webOutDir "*") $WebExportDir -Recurse -Force
}
else {
    Write-Warning "Folderul apps\web\out nu există. Dacă build-ul tău nu exportă static automat, verifică fluxul web-export."
}

Write-Host ""
Write-Host "=== BUILD TAURI RELEASE ==="

Set-Location $TauriDir
cargo tauri build

$nsisPath = Join-Path $TauriDir "target\release\bundle\nsis\Chilipir_0.1.0_x64-setup.exe"
$msiPath  = Join-Path $TauriDir "target\release\bundle\msi\Chilipir_0.1.0_x64_en-US.msi"

Write-Host ""
Write-Host "=== ARTEFACTE ==="
if (Test-Path $nsisPath) {
    Get-Item $nsisPath | Select-Object FullName, Length, LastWriteTime
}
if (Test-Path $msiPath) {
    Get-Item $msiPath | Select-Object FullName, Length, LastWriteTime
}

Write-Host ""
Write-Host "=== STOP APP VECHE ==="
Get-Process -Name "price-watch-api","price-watch-ro-desktop","Chilipir","chrome" -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "=== REINSTALL ==="
if (-not (Test-Path $nsisPath)) {
    throw "Nu am găsit installerul NSIS: $nsisPath"
}

Start-Process $nsisPath

Write-Host ""
Write-Host "=== GATA ==="
Write-Host "EXE installer: $nsisPath"
Write-Host "MSI installer: $msiPath"
