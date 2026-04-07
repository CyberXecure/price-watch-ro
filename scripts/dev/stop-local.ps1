$ErrorActionPreference = "SilentlyContinue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = [System.IO.Path]::GetFullPath((Join-Path $ScriptDir "..\..\"))
$ApiDir = Join-Path $ProjectRoot "services\api"
$WebDir = Join-Path $ProjectRoot "apps\web"
$ChromeProfile = Join-Path $env:TEMP "price-watch-ro-chrome"

function Get-ProcList {
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue
}

function Stop-ProcessTree {
    param(
        [Parameter(Mandatory = $true)]
        [int]$ProcessId
    )

    $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $ProcessId" -ErrorAction SilentlyContinue
    foreach ($child in $children) {
        Stop-ProcessTree -ProcessId $child.ProcessId
    }

    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($proc) {
        try {
            Stop-Process -Id $ProcessId -Force -ErrorAction Stop
        }
        catch {
        }
    }
}

function Get-ApiProcesses {
    $apiDirEscaped = [Regex]::Escape($ApiDir)

    Get-ProcList | Where-Object {
        $_.CommandLine -and (
            $_.CommandLine -match 'uvicorn\s+app\.main:app' -or
            $_.CommandLine -match $apiDirEscaped
        )
    }
}

function Get-WebProcesses {
    $webDirEscaped = [Regex]::Escape($WebDir)

    Get-ProcList | Where-Object {
        $_.CommandLine -and (
            $_.CommandLine -match $webDirEscaped -or
            $_.CommandLine -match 'npm\s+run\s+dev' -or
            $_.CommandLine -match 'next(\.cmd)?\s+dev'
        )
    }
}

function Get-ChromeDebugProcesses {
    $profileEscaped = [Regex]::Escape($ChromeProfile)

    Get-ProcList | Where-Object {
        $_.CommandLine -and
        $_.Name -match '^(chrome|msedge)\.exe$' -and
        $_.CommandLine -match '--remote-debugging-port=9222' -and
        $_.CommandLine -match $profileEscaped
    }
}

function Stop-MatchedProcesses {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,

        [Parameter(Mandatory = $true)]
        [object[]]$Processes
    )

    if (-not $Processes -or $Processes.Count -eq 0) {
        Write-Host "Nu există procese $Label de oprit."
        return
    }

    $unique = $Processes | Sort-Object ProcessId -Unique

    foreach ($proc in $unique) {
        Write-Host "Oprire $Label -> PID $($proc.ProcessId) [$($proc.Name)]"
        Stop-ProcessTree -ProcessId $proc.ProcessId
    }
}

Write-Host "=== STOP procese locale price-watch-ro ==="

$apiProcesses = Get-ApiProcesses
$webProcesses = Get-WebProcesses
$chromeProcesses = Get-ChromeDebugProcesses

Stop-MatchedProcesses -Label "API" -Processes $apiProcesses
Stop-MatchedProcesses -Label "Web" -Processes $webProcesses
Stop-MatchedProcesses -Label "Chrome debug" -Processes $chromeProcesses

Start-Sleep -Seconds 1

Write-Host ""
Write-Host "Verificare finală:"

foreach ($port in 8000, 3000, 9222) {
    $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($conn) {
        Write-Warning "Portul $port este încă ocupat."
    }
    else {
        Write-Host "Portul $port este liber."
    }
}