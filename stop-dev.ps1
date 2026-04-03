$ErrorActionPreference = "SilentlyContinue"

Write-Host "=== STOP procese pe porturile 8000 / 3000 / 9222 ==="

$ports = @(8000, 3000, 9222)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connections) {
        $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($procId in $pids) {
            try {
                Stop-Process -Id $procId -Force
                Write-Host "Oprit PID $procId pe portul $port"
            } catch {}
        }
    } else {
        Write-Host "Niciun proces pe portul $port"
    }
}

Write-Host ""
Write-Host "=== STOP chrome.exe ==="
try {
    taskkill /F /IM chrome.exe | Out-Null
    Write-Host "Chrome oprit."
} catch {
    Write-Host "Chrome nu era pornit."
}

Write-Host ""
Write-Host "=== GATA ==="