$ErrorActionPreference = "SilentlyContinue"  
  
$ProjectRoot = "D:\dev\projects\price-watch-ro"  
$ApiDir = Join-Path $ProjectRoot "services\api"  
$WebDir = Join-Path $ProjectRoot "apps\web"  
$ChromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"  
$ChromeProfile = "D:\dev\chrome-freshful-debug"  
  
Write-Host "=== STOP procese vechi pe porturile 8000 / 3000 / 9222 ==="  
  
$ports = @(8000, 3000, 9222)  
foreach ($port in $ports) {  
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue  
    if ($connections) {  
        $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique  
        foreach ($procId in $pids) {  
            try {  
                Stop-Process -Id $procId -Force -ErrorAction Stop  
                Write-Host "Oprit PID $procId pe portul $port"  
            } catch {}  
        }  
    } else {  
        Write-Host "Niciun proces pe portul $port"  
    }  
}  
  
Write-Host ""  
Write-Host "=== STOP procese Chrome existente ==="  
try {  
    taskkill /F /IM chrome.exe | Out-Null  
    Write-Host "Chrome vechi oprit."  
} catch {  
    Write-Host "Chrome nu era pornit."  
}  
  
Start-Sleep -Seconds 2  
  
Write-Host ""  
Write-Host "=== PORNIRE Chrome cu CDP ==="  
if (-not (Test-Path $ChromePath)) {  
    Write-Host "Chrome nu a fost gasit la: $ChromePath"  
    exit  
}  
  
Start-Process -FilePath $ChromePath -ArgumentList @(  
    "--remote-debugging-port=9222",  
    "--user-data-dir=$ChromeProfile",  
    "--new-window",  
    "about:blank"  
)  
  
Start-Sleep -Seconds 4  
  
Write-Host ""  
Write-Host "=== VERIFICARE CDP ==="  
try {  
    $cdp = Invoke-RestMethod -Uri "http://127.0.0.1:9222/json/version"  
    Write-Host "Chrome CDP OK:" $cdp.Browser  
} catch {  
    Write-Host "CDP NU raspunde pe 9222."  
}  
  
Write-Host ""  
Write-Host "=== PORNIRE API ==="  
Start-Process powershell -ArgumentList @(  
    "-NoExit",  
    "-Command",  
    "Set-Location '$ApiDir'; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload"  
)  
  
Write-Host "Astept pornirea API..."  
Start-Sleep -Seconds 10  
  
Write-Host ""  
Write-Host "=== VERIFICARE API ==="  
$apiOk = $false  
for ($i = 1; $i -le 10; $i++) {  
    try {  
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2  
        Write-Host "API OK"  
        $health | Format-List  
        $apiOk = $true  
        break  
    } catch {  
        Start-Sleep -Seconds 2  
    }  
}  
if (-not $apiOk) {  
    Write-Host "API nu raspunde inca pe 8000."  
}  
  
Write-Host ""  
Write-Host "=== PORNIRE FRONTEND ==="  
Start-Process powershell -ArgumentList @(  
    "-NoExit",  
    "-Command",  
    "Set-Location '$WebDir'; npm run dev"  
)  
  
Start-Sleep -Seconds 6  
  
Write-Host ""  
Write-Host "=== GATA ==="  
Write-Host "Chrome debug: http://127.0.0.1:9222/json/version"  
Write-Host "API:          http://127.0.0.1:8000"  
Write-Host "Frontend:     http://localhost:3000"  
Write-Host "Deschide manual aplicatia: http://localhost:3000/lists/1"  
