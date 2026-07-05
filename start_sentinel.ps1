$ErrorActionPreference = "Stop"

$scriptPath = $MyInvocation.MyCommand.Path
if (-not $env:SENTINEL_HIDDEN_LAUNCH -and $scriptPath) {
    $env:SENTINEL_HIDDEN_LAUNCH = "1"
    Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $scriptPath) -WindowStyle Hidden
    exit 0
}

$projectRoot = "C:\Users\bloxd\Documents\GitHub\Sentinel"
$backendDir = Join-Path $projectRoot "risk-engine"
$frontendPath = Join-Path $projectRoot "frontend\index.html"
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

$env:AI_PROVIDER = "ollama"
$env:OLLAMA_MODEL = "llama3:latest"
$env:OLLAMA_HOST = "http://127.0.0.1:11434"
$env:REDIS_URL = "redis://localhost:6379/0"

function Stop-SentinelProcesses {
    $sentinelProcesses = Get-CimInstance Win32_Process |
        Where-Object {
            $_.Name -in @("python.exe", "pythonw.exe", "uvicorn.exe") -and (
                $_.CommandLine -like "*app.main:app*" -or
                $_.CommandLine -like "*risk-engine*" -or
                $_.CommandLine -like "*Sentinel*"
            )
        }

    foreach ($proc in $sentinelProcesses) {
        try {
            Stop-Process -Id $proc.ProcessId -Force -ErrorAction Stop
            Write-Host "Stopped previous Sentinel process $($proc.ProcessId)"
        } catch {
            Write-Host "Could not stop process $($proc.ProcessId): $($_.Exception.Message)"
        }
    }
}

if (-not (Test-Path $backendDir)) {
    Write-Error "Backend directory not found: $backendDir"
    exit 1
}

if (-not (Test-Path $venvPython)) {
    Write-Error "Virtual environment Python not found: $venvPython"
    exit 1
}

Stop-SentinelProcesses

Set-Location $backendDir

Write-Host "Starting Sentinel backend..."
Write-Host "Using Redis: $env:REDIS_URL"
Write-Host "Using Ollama: $env:OLLAMA_HOST/$env:OLLAMA_MODEL"

$backendProcess = Start-Process -FilePath $venvPython -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000") -WorkingDirectory $backendDir -PassThru

$backendReady = $false
for ($attempt = 1; $attempt -le 30; $attempt++) {
    Start-Sleep -Seconds 1
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/" -Method Get -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            break
        }
    } catch {
        # Keep retrying until the backend responds.
    }
}

if (-not $backendReady) {
    Write-Error "The backend did not become reachable within 30 seconds."
    if ($backendProcess) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    exit 1
}

Start-Process -FilePath $frontendPath

Write-Host "Backend started. Open the frontend to chat with the local model."
exit 0

