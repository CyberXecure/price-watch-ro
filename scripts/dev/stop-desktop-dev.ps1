$ErrorActionPreference = "SilentlyContinue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = [System.IO.Path]::GetFullPath((Join-Path $ScriptDir "..\..\"))

$StopLocalScript = Join-Path $ProjectRoot "scripts\dev\stop-local.ps1"

function Stop-TauriProcesses {
    Write-Host "=== Oprire procese Tauri / cargo ==="

    $processNames = @(
        "price-watch-ro-desktop",
        "cargo"
    )

    foreach ($name in $processNames) {
        $procs = Get-Process -Name $name -ErrorAction SilentlyContinue
        foreach ($proc in $procs) {
            try {
                Write-Host "Oprire $name -> PID $($proc.Id)"
                Stop-Process -Id $proc.Id -Force -ErrorAction Stop
            }
            catch {
                Write-Warning "Nu am putut opri $name -> PID $($proc.Id)"
            }
        }
    }

    $tauriRelated = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -and (
            $_.CommandLine -match 'cargo run' -or
            $_.CommandLine -match 'src-tauri'
        )
    }

    foreach ($proc in ($tauriRelated | Sort-Object ProcessId -Unique)) {
        try {
            Write-Host "Oprire proces asociat Tauri -> PID $($proc.ProcessId)"
            Stop-Process -Id $proc.ProcessId -Force -ErrorAction Stop
        }
        catch {
            Write-Warning "Nu am putut opri PID $($proc.ProcessId)"
        }
    }
}

Write-Host "=== STOP DESKTOP DEV price-watch-ro ==="

Stop-TauriProcesses

if (Test-Path $StopLocalScript) {
    Write-Host "=== Oprire stack local (API + Web + Chrome debug) ==="
    & $StopLocalScript
}
else {
    Write-Warning "Nu am găsit: $StopLocalScript"
}

Write-Host ""
Write-Host "=== Gata ==="
