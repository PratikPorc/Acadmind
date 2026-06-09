# Rebuild and restart all Docker services
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "Restarting Docker services..." -ForegroundColor Cyan
docker compose down
docker compose up -d --build --force-recreate

Write-Host "Waiting for Neo4j..." -ForegroundColor Cyan
$attempts = 0
while ($attempts -lt 30) {
    $health = docker inspect --format='{{.State.Health.Status}}' acadmind-neo4j 2>$null
    if ($health -eq "healthy") { break }
    Start-Sleep -Seconds 2
    $attempts++
}

Write-Host "Applying Neo4j constraints..." -ForegroundColor Cyan
Get-Content backend\scripts\init_neo4j.cypher | docker exec -i acadmind-neo4j cypher-shell -u neo4j -p acadmind_dev_password

Write-Host "Docker ready." -ForegroundColor Green
docker compose ps
