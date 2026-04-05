$Ports = @(8000, 3000, 9222)
$ProcessIds = New-Object System.Collections.Generic.HashSet[int]

foreach ($Port in $Ports) {
    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    foreach ($connection in $connections) {
        if ($connection.OwningProcess -and $connection.OwningProcess -ne 0) {
            [void]$ProcessIds.Add([int]$connection.OwningProcess)
        }
    }
}

if ($ProcessIds.Count -eq 0) {
    Write-Host "Nu există procese active pe porturile 8000, 3000, 9222."
    exit
}

foreach ($ProcessId in $ProcessIds) {
    try {
        Stop-Process -Id $ProcessId -Force -ErrorAction Stop
        Write-Host "Oprit PID $ProcessId"
    }
    catch {
        Write-Warning "Nu am putut opri PID $ProcessId"
    }
}
