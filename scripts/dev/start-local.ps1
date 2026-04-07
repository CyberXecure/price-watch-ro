$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = [System.IO.Path]::GetFullPath((Join-Path $ScriptDir "..\..\"))
$ApiDir = Join-Path $ProjectRoot "services\api"
$WebDir = Join-Path $ProjectRoot "apps\web"

$ChromeProfile = Join-Path $env:TEMP "price-watch-ro-chrome"
$ResetChromeProfile = $false
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

function Get-ShellPath {
    $pwsh = (Get-Command pwsh.exe -ErrorAction SilentlyContinue).Source
    if ($pwsh) { return $pwsh }

    $powershell = (Get-Command powershell.exe -ErrorAction SilentlyContinue).Source
    if ($powershell) { return $powershell }

    throw "Nu am găsit nici pwsh.exe, nici powershell.exe."
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
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
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

function Show-PortUsage {
    param(
        [Parameter(Mandatory = $true)]
        [int[]]$Ports
    )

    foreach ($port in $Ports) {
        $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($conn) {
            Write-Warning "Portul $port este deja ocupat de PID $($conn.OwningProcess)."
        }
        else {
            Write-Host "Portul $port este liber."
        }
    }
}

function Stop-ChromeDebugProfile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ProfilePath
    )

    $escapedProfile = [Regex]::Escape($ProfilePath)

    $procs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -and
        $_.Name -match '^(chrome|msedge)\.exe$' -and
        $_.CommandLine -match '--remote-debugging-port=9222' -and
        $_.CommandLine -match $escapedProfile
    }

    if (-not $procs) {
        Write-Host "Nu există browser debug price-watch-ro de oprit."
        return
    }

    foreach ($proc in ($procs | Sort-Object ProcessId -Unique)) {
        Write-Host "Oprire browser debug stale -> PID $($proc.ProcessId) [$($proc.Name)]"
        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
    }

    Start-Sleep -Seconds 1
}

function Start-ChromeDebug {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ChromePath,

        [Parameter(Mandatory = $true)]
        [string]$ProfilePath
    )

    if ($ResetChromeProfile -and (Test-Path $ProfilePath)) {
        try {
            Remove-Item -Path $ProfilePath -Recurse -Force -ErrorAction Stop
            Write-Host "Profilul Chrome de debug a fost resetat: $ProfilePath"
        }
        catch {
            Write-Warning "Nu am putut șterge profilul Chrome de debug. Închide browserul pornit pe acest profil și rulează din nou scriptul."
        }
    }

    $chromeArgs = @(
        "--remote-debugging-port=9222",
        "--user-data-dir=$ProfilePath",
        "--lang=ro",
        "--accept-lang=ro-RO,ro"
    )

    Start-Process -FilePath $ChromePath -ArgumentList $chromeArgs | Out-Null
    Write-Host "Chrome pornit cu remote debugging pe 9222, în limba română."
}

Write-Host "=== START price-watch-ro ==="
Show-PortUsage -Ports @(9222, 8000, 3000)

$ShellPath = Get-ShellPath

$chromePath = Get-ChromePath
if (-not $chromePath) {
    Write-Warning "Chrome nu a fost găsit automat. Pentru refresh rendered, pornește-l manual cu --remote-debugging-port=9222 --lang=ro --accept-lang=ro-RO,ro."
}
else {
    $port9222Open = Test-TcpPort -HostName "127.0.0.1" -Port 9222
    $cdpHealthy = Test-HttpOk -Url $ChromeCdpUrl

    if ($cdpHealthy) {
        Write-Host "[OK] Există deja un browser debug activ și valid pe 9222. Nu pornesc alt Chrome."
    }
    elseif ($port9222Open) {
        Write-Warning "Portul 9222 este ocupat, dar CDP nu răspunde. Repornez sesiunea Chrome de debug."
        Stop-ChromeDebugProfile -ProfilePath $ChromeProfile
        Start-ChromeDebug -ChromePath $chromePath -ProfilePath $ChromeProfile
        [void](Wait-HttpOk -Url $ChromeCdpUrl -TimeoutSeconds 15 -Label "Chrome CDP")
    }
    else {
        Start-ChromeDebug -ChromePath $chromePath -ProfilePath $ChromeProfile
        [void](Wait-HttpOk -Url $ChromeCdpUrl -TimeoutSeconds 15 -Label "Chrome CDP")
    }
}

$apiPython = Join-Path $ApiDir ".venv\Scripts\python.exe"
if (-not (Test-Path $apiPython)) {
    $apiPython = "python"
    Write-Warning "Nu am găsit .venv local pentru API. Folosesc python din PATH."
}

$apiCommand = "Set-Location '$ApiDir'; & '$apiPython' -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

$apiProcess = Start-Process -FilePath $ShellPath -ArgumentList @(
    "-NoExit",
    "-Command",
    $apiCommand
) -PassThru

Write-Host "API shell pornit. PID launcher: $($apiProcess.Id)"
[void](Wait-HttpOk -Url "http://127.0.0.1:8000/health" -TimeoutSeconds 25 -Label "API")

$webCommand = "Set-Location '$WebDir'; `$env:NEXT_PUBLIC_API_BASE='http://127.0.0.1:8000'; npm run dev"

$webProcess = Start-Process -FilePath $ShellPath -ArgumentList @(
    "-NoExit",
    "-Command",
    $webCommand
) -PassThru

Write-Host "Web shell pornit. PID launcher: $($webProcess.Id)"
[void](Wait-TcpPort -HostName "127.0.0.1" -Port 3000 -TimeoutSeconds 30 -Label "Web")

Write-Host ""
Write-Host "=== REZUMAT ==="
Write-Host "API:    http://127.0.0.1:8000"
Write-Host "Health: http://127.0.0.1:8000/health"
Write-Host "Rendered: http://127.0.0.1:8000/health/rendered"
Write-Host "Web:    http://localhost:3000"
Write-Host "CDP:    http://127.0.0.1:9222/json/version"
Write-Host "Chrome debug profile: $ChromeProfile"