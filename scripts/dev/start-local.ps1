$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = [System.IO.Path]::GetFullPath((Join-Path $ScriptDir "..\..\"))

$ApiDir = Join-Path $ProjectRoot "services\api"
$WebDir = Join-Path $ProjectRoot "apps\web"

$ChromeProfile = Join-Path $env:LOCALAPPDATA "PriceWatchRO\chrome-cdp-dev-no-extensions"
$ChromeCdpUrl = "http://127.0.0.1:9222/json/version"

function Get-ChromePath {
    $candidates = @(
        "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
        "$env:ProgramFiles(x86)\Google\Chrome\Application\chrome.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

function Test-TcpPort {
    param(
        [Parameter(Mandatory = $true)]
        [string]$HostName,

        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    try {
        $client = [System.Net.Sockets.TcpClient]::new()
        $async = $client.BeginConnect($HostName, $Port, $null, $null)
        $ok = $async.AsyncWaitHandle.WaitOne(1000, $false)

        if (-not $ok) {
            $client.Close()
            return $false
        }

        $client.EndConnect($async)
        $client.Close()
        return $true
    }
    catch {
        return $false
    }
}

function Wait-TcpPort {
    param(
        [Parameter(Mandatory = $true)]
        [string]$HostName,

        [Parameter(Mandatory = $true)]
        [int]$Port,

        [Parameter(Mandatory = $true)]
        [int]$TimeoutSeconds,

        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    while ((Get-Date) -lt $deadline) {
        if (Test-TcpPort -HostName $HostName -Port $Port) {
            Write-Host "[OK] $Label este disponibil pe $HostName`:$Port"
            return $true
        }

        Start-Sleep -Milliseconds 500
    }

    Write-Warning "[FAIL] $Label nu a devenit disponibil pe $HostName`:$Port în $TimeoutSeconds sec."
    return $false
}

function Test-HttpOk {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url
    )

    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
        return ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400)
    }
    catch {
        return $false
    }
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
        if (Test-HttpOk -Url $Url) {
            Write-Host "[OK] $Label răspunde la $Url"
            return $true
        }

        Start-Sleep -Milliseconds 500
    }

    Write-Warning "[FAIL] $Label nu răspunde la $Url în $TimeoutSeconds sec."
    return $false
}

function Stop-ProcessesOnPorts {
    param(
        [Parameter(Mandatory = $true)]
        [int[]]$Ports
    )

    foreach ($port in $Ports) {
        $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        foreach ($connection in $connections) {
            try {
                Stop-Process -Id $connection.OwningProcess -Force -ErrorAction Stop
                Write-Host "Am oprit PID $($connection.OwningProcess) de pe portul $port."
            }
            catch {
                Write-Warning "Nu am putut opri PID $($connection.OwningProcess) de pe portul $port."
            }
        }
    }
}

function Test-PromoEngineCdp {
    try {
        $result = Invoke-RestMethod -Uri $ChromeCdpUrl -Method Get -TimeoutSec 3
        return ($null -ne $result.webSocketDebuggerUrl)
    }
    catch {
        return $false
    }
}

function Ensure-ChromeCdp {
    if (Test-PromoEngineCdp) {
        Write-Host "[OK] Chrome CDP deja disponibil pe 9222."
        return
    }

    $chromePath = Get-ChromePath
    if (-not $chromePath) {
        throw "Nu am găsit chrome.exe."
    }

    Write-Host "Pornesc Chrome cu remote debugging pe 9222..."
    Start-Process -FilePath $chromePath -ArgumentList @(
        "--remote-debugging-port=9222",
        "--user-data-dir=$ChromeProfile",
        "--disable-extensions",
        "--disable-component-extensions-with-background-pages",
        "--disable-default-apps",
        "--disable-sync",
        "--no-first-run",
        "--no-default-browser-check",
        "--lang=ro",
        "--accept-lang=ro-RO,ro"
    ) | Out-Null

    [void](Wait-HttpOk -Url $ChromeCdpUrl -TimeoutSeconds 15 -Label "Chrome CDP")
}

function Stop-WebDevProcesses {
    Write-Host "=== Curăț procese frontend vechi (3000 / 3001) ==="
    Stop-ProcessesOnPorts -Ports @(3000, 3001)

    $lockPath = Join-Path $WebDir ".next\dev\lock"
    if (Test-Path $lockPath) {
        Remove-Item $lockPath -Force -ErrorAction SilentlyContinue
        Write-Host "Am șters lock-ul Next.js: $lockPath"
    }
}

Write-Host "=== START price-watch-ro ==="

Ensure-ChromeCdp

$apiPython = Join-Path $ApiDir ".venv\Scripts\python.exe"
if (-not (Test-Path $apiPython)) {
    throw "Nu am găsit Python-ul din venv: $apiPython"
}

Write-Host "=== Curăț API vechi (18400) ==="
Stop-ProcessesOnPorts -Ports @(18400)

$apiProcess = Start-Process -FilePath $apiPython -ArgumentList @(
    ".\run-desktop.py"
) -WorkingDirectory $ApiDir -PassThru

Write-Host "API pornit. PID: $($apiProcess.Id)"
[void](Wait-HttpOk -Url "http://127.0.0.1:18400/health" -TimeoutSeconds 25 -Label "API")

Stop-WebDevProcesses

$npmCmd = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not $npmCmd) {
    throw "Nu am găsit npm.cmd în PATH."
}

$webProcess = Start-Process -FilePath $npmCmd -ArgumentList @(
    "run",
    "dev"
) -WorkingDirectory $WebDir -Environment @{
    NEXT_PUBLIC_API_BASE = "http://127.0.0.1:18400"
} -PassThru

Write-Host "Web pornit. PID: $($webProcess.Id)"
if (-not (Wait-TcpPort -HostName "127.0.0.1" -Port 3000 -TimeoutSeconds 20 -Label "Web 3000")) {
    [void](Wait-TcpPort -HostName "127.0.0.1" -Port 3001 -TimeoutSeconds 15 -Label "Web 3001")
}

Write-Host ""
Write-Host "=== REZUMAT ==="
Write-Host "API:         http://127.0.0.1:18400"
Write-Host "Health:      http://127.0.0.1:18400/health"
Write-Host "PromoEngine: http://127.0.0.1:18400/health/promo-engine"
Write-Host "Web:         http://localhost:3000 sau http://localhost:3001"
Write-Host "CDP:         $ChromeCdpUrl"
Write-Host "Chrome profile: $ChromeProfile"
