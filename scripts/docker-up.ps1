# Start full stack: Neo4j, Redis, backend, frontend
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Test-Path "backend\.env")) {
    Write-Host "Missing backend\.env — copy from backend\.env.example and fill in keys." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path "frontend\.env.local")) {
    Write-Host "Missing frontend\.env.local — copy from frontend\.env.example and fill in keys." -ForegroundColor Red
    exit 1
}

Write-Host "Starting AcadMind stack (docker compose)..." -ForegroundColor Cyan
docker compose up -d --build

Write-Host "Waiting for services..." -ForegroundColor Cyan
$attempts = 0
while ($attempts -lt 60) {
    $backend = docker inspect --format='{{.State.Health.Status}}' acadmind-backend 2>$null
    if ($backend -eq "healthy") { break }
    Start-Sleep -Seconds 2
    $attempts++
}

Write-Host ""
Write-Host "AcadMind is ready:" -ForegroundColor Green
Write-Host "  Frontend   http://localhost:5173"
Write-Host "  Backend    http://localhost:8000"
Write-Host "  API docs   http://localhost:8000/docs"
Write-Host "  Neo4j      http://localhost:7474"
Write-Host ""
docker compose ps
