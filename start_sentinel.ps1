$ErrorActionPreference = "Stop"

$projectRoot = "C:\Users\bloxd\Documents\GitHub\Sentinel"
$backendDir = Join-Path $projectRoot "risk-engine"
$frontendPath = Join-Path $projectRoot "frontend\index.html"

$env:AI_PROVIDER = "ollama"
$env:OLLAMA_MODEL = "llama3:latest"
$env:OLLAMA_HOST = "http://localhost:11434"
$env:REDIS_URL = "redis://localhost:6379/0"

if (-not (Test-Path $backendDir)) {
    Write-Error "Backend directory not found: $backendDir"
    exit 1
}

Set-Location $backendDir

$pythonExe = "C:\Users\bloxd\AppData\Local\Python\pythoncore-3.14-64\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

Write-Host "Starting Sentinel backend..."
Write-Host "Using Redis: $env:REDIS_URL"
Write-Host "Using Ollama: $env:OLLAMA_HOST/$env:OLLAMA_MODEL"

Start-Process -FilePath $pythonExe -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000") -WorkingDirectory $backendDir -WindowStyle Normal
Start-Process -FilePath $frontendPath

Write-Host "Backend started. The frontend should open in your browser."

