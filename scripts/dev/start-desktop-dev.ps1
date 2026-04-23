$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = [System.IO.Path]::GetFullPath((Join-Path $ScriptDir "..\..\"))

$StartLocalScript = Join-Path $ProjectRoot "scripts\dev\start-local.ps1"
$TauriDir = Join-Path $ProjectRoot "desktop\src-tauri"

function Get-ShellPath {
    $pwsh = (Get-Command pwsh.exe -ErrorAction SilentlyContinue).Source
    if ($pwsh) { return $pwsh }

    $powershell = (Get-Command powershell.exe -ErrorAction SilentlyContinue).Source
    if ($powershell) { return $powershell }

    throw "Nu am găsit nici pwsh.exe, nici powershell.exe."
}

function Wait-HttpOk {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url,

        [Parameter(Mandatory = $true)]
        [int]$TimeoutSeconds,

        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
                Write-Host "[OK] $Label răspunde la $Url"
                return $true
            }
        }
        catch {
        }

        Start-Sleep -Milliseconds 500
    }

    throw "$Label nu răspunde la $Url în $TimeoutSeconds sec."
}

Write-Host "=== START DESKTOP DEV price-watch-ro ==="

if (-not (Test-Path $StartLocalScript)) {
    throw "Nu am găsit scriptul: $StartLocalScript"
}

$ShellPath = Get-ShellPath

Write-Host "=== Pornesc stack local (Chrome + API + Web) ==="
$localProcess = Start-Process -FilePath $ShellPath -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$ProjectRoot'; & '$StartLocalScript'"
) -PassThru

Write-Host "Launcher start-local pornit. PID: $($localProcess.Id)"

[void](Wait-HttpOk -Url "http://127.0.0.1:18400/health" -TimeoutSeconds 30 -Label "API")
try {
    [void](Wait-HttpOk -Url "http://127.0.0.1:3000" -TimeoutSeconds 20 -Label "Web 3000")
}
catch {
    [void](Wait-HttpOk -Url "http://127.0.0.1:3001" -TimeoutSeconds 20 -Label "Web 3001")
}

Write-Host "=== Pornesc Tauri desktop ==="
$tauriCommand = "Set-Location '$TauriDir'; cargo run"

$tauriProcess = Start-Process -FilePath $ShellPath -ArgumentList @(
    "-NoExit",
    "-Command",
    $tauriCommand
) -PassThru

Write-Host "Tauri launcher pornit. PID: $($tauriProcess.Id)"

Write-Host ""
Write-Host "=== REZUMAT ==="
Write-Host "API:    http://127.0.0.1:18400"
Write-Host "Web:    http://localhost:3000 sau http://localhost:3001"
Write-Host "Desktop: pornit prin cargo run"
