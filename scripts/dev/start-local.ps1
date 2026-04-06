$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = [System.IO.Path]::GetFullPath((Join-Path $ScriptDir "..\..\"))
$ApiDir = Join-Path $ProjectRoot "services\api"
$WebDir = Join-Path $ProjectRoot "apps\web"

$ChromeProfile = Join-Path $env:TEMP "price-watch-ro-chrome"
$ResetChromeProfile = $false

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
    if ($pwsh) {
        return $pwsh
    }

    $powershell = (Get-Command powershell.exe -ErrorAction SilentlyContinue).Source
    if ($powershell) {
        return $powershell
    }

    throw "Nu am găsit nici pwsh.exe, nici powershell.exe."
}

$ShellPath = Get-ShellPath

$chromePath = Get-ChromePath
if ($chromePath) {
    if ($ResetChromeProfile -and (Test-Path $ChromeProfile)) {
        try {
            Remove-Item -Path $ChromeProfile -Recurse -Force -ErrorAction Stop
            Write-Host "Profilul Chrome de debug a fost resetat: $ChromeProfile"
        }
        catch {
            Write-Warning "Nu am putut șterge profilul Chrome de debug. Închide toate ferestrele Chrome pornite din acest profil și rulează din nou scriptul."
        }
    }

    $chromeArgs = @(
        "--remote-debugging-port=9222",
        "--user-data-dir=$ChromeProfile",
        "--lang=ro",
        "--accept-lang=ro-RO,ro"
    )

    Start-Process -FilePath $chromePath -ArgumentList $chromeArgs | Out-Null
    Write-Host "Chrome pornit cu remote debugging pe 9222, în limba română."
}
else {
    Write-Warning "Chrome nu a fost găsit automat. Pentru refresh rendered, pornește-l manual cu --remote-debugging-port=9222 --lang=ro --accept-lang=ro-RO,ro."
}

$apiPython = Join-Path $ApiDir ".venv\Scripts\python.exe"
if (-not (Test-Path $apiPython)) {
    $apiPython = "python"
}

Start-Process -FilePath $ShellPath -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$ApiDir'; & '$apiPython' -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
) | Out-Null

Start-Sleep -Seconds 2

Start-Process -FilePath $ShellPath -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$WebDir'; `$env:NEXT_PUBLIC_API_BASE='http://127.0.0.1:8000'; npm run dev"
) | Out-Null

Write-Host ""
Write-Host "API: http://127.0.0.1:8000"
Write-Host "Web: http://localhost:3000"
Write-Host "Chrome debug profile: $ChromeProfile"