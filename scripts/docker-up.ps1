# Start Neo4j + Redis and apply graph constraints
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "Starting Docker services..." -ForegroundColor Cyan
docker compose up -d --build

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

Write-Host "Docker ready: Neo4j http://localhost:7474 | Redis localhost:6379" -ForegroundColor Green
docker compose ps
