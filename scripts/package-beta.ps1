param(
    [string]$ZipName = "price-watch-ro-beta-fixed-clean-2026-04-11.zip"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$TempDir = Join-Path $env:TEMP "price-watch-ro-package"
$ZipPath = Join-Path $ProjectRoot $ZipName

Write-Host "=== PACKAGE beta clean ZIP ==="

if (Test-Path $TempDir) {
    Remove-Item $TempDir -Recurse -Force
}

New-Item -ItemType Directory -Path $TempDir | Out-Null

$itemsToCopy = @(
    "apps",
    "services",
    "scripts",
    "README-beta.md",
    "BETA-CHECKLIST.md",
    "README.md",
    "LICENSE",
    ".env.example",
    ".gitignore"
)

foreach ($item in $itemsToCopy) {
    $source = Join-Path $ProjectRoot $item
    if (Test-Path $source) {
        Copy-Item $source -Destination $TempDir -Recurse -Force
        Write-Host "[COPIAT] $item"
    }
    else {
        Write-Host "[LIPSĂ]  $item"
    }
}

$pathsToRemove = @(
    "$TempDir\apps\web\.next",
    "$TempDir\apps\web\node_modules",
    "$TempDir\services\api\.venv"
)

foreach ($path in $pathsToRemove) {
    if (Test-Path $path) {
        Remove-Item $path -Recurse -Force
        Write-Host "[ȘTERS]  $path"
    }
}

Get-ChildItem -Path $TempDir -Recurse -Directory -Force |
    Where-Object { $_.Name -in @("__pycache__", ".pytest_cache") } |
    ForEach-Object {
        Remove-Item $_.FullName -Recurse -Force
        Write-Host "[ȘTERS]  $($_.FullName)"
    }

Get-ChildItem -Path $TempDir -Recurse -File -Force |
    Where-Object {
        $_.Extension -in @(".pyc", ".pyo", ".db", ".log") -or
        $_.Name -in @("Thumbs.db", ".DS_Store")
    } |
    ForEach-Object {
        Remove-Item $_.FullName -Force
        Write-Host "[ȘTERS]  $($_.FullName)"
    }

if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}

Compress-Archive -Path "$TempDir\*" -DestinationPath $ZipPath -CompressionLevel Optimal

Write-Host ""
Write-Host "ZIP curat creat:"
Write-Host $ZipPath
