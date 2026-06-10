# Rebuild and restart the full Docker stack
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "Restarting AcadMind stack..." -ForegroundColor Cyan
docker compose down
& "$PSScriptRoot\docker-up.ps1"
