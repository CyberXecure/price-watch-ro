$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = [System.IO.Path]::GetFullPath((Join-Path $ScriptDir "..\..\"))
$ApiDir = Join-Path $ProjectRoot "services\api"
$WebDir = Join-Path $ProjectRoot "apps\web"

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

$chromePath = Get-ChromePath
if ($chromePath) {
    Start-Process -FilePath $chromePath -ArgumentList @(
        "--remote-debugging-port=9222",
        "--user-data-dir=$env:TEMP\price-watch-ro-chrome"
    ) | Out-Null

    Write-Host "Chrome pornit cu remote debugging pe 9222."
}
else {
    Write-Warning "Chrome nu a fost găsit automat. Pentru refresh rendered, pornește-l manual cu --remote-debugging-port=9222."
}

$apiPython = Join-Path $ApiDir ".venv\Scripts\python.exe"
if (-not (Test-Path $apiPython)) {
    $apiPython = "python"
}

Start-Process -FilePath "powershell.exe" -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$ApiDir'; & '$apiPython' -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
) | Out-Null

Start-Sleep -Seconds 2

Start-Process -FilePath "powershell.exe" -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$WebDir'; `$env:NEXT_PUBLIC_API_BASE='http://127.0.0.1:8000'; npm run dev"
) | Out-Null

Write-Host ""
Write-Host "API: http://127.0.0.1:8000"
Write-Host "Web: http://localhost:3000"
