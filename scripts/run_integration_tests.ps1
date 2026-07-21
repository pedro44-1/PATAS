param(
    [string]$ComposeFile = "docker-compose.test.yml",
    [string]$ProjectName = "patas-test"
)

$ErrorActionPreference = "Stop"

Write-Host "=== PATAS Integration Test Runner ===" -ForegroundColor Cyan
Write-Host ""

function Cleanup {
    Write-Host "`nTearing down test stack..." -ForegroundColor Yellow
    docker compose -f $ComposeFile -p $ProjectName down --volumes --remove-orphans 2>$null
}

try {
    Cleanup

    Write-Host "Starting Docker Compose test stack..." -ForegroundColor Green
    docker compose -f $ComposeFile -p $ProjectName up -d --build

    Write-Host "Waiting for backend to be ready..." -ForegroundColor Yellow
    $maxRetries = 30
    $retry = 0
    while ($retry -lt $maxRetries) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8001/health" -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -eq 200) {
                Write-Host "Backend is ready!" -ForegroundColor Green
                break
            }
        } catch {
            # Not ready yet
        }
        $retry++
        Write-Host "  Waiting... ($retry/$maxRetries)" -NoNewline
        Start-Sleep -Seconds 2
    }

    if ($retry -ge $maxRetries) {
        Write-Host "Backend failed to start in time." -ForegroundColor Red
        docker compose -f $ComposeFile -p $ProjectName logs backend_test
        exit 1
    }

    Write-Host "`nRunning integration tests..." -ForegroundColor Green
    $env:BASE_URL = "http://localhost:8001"
    cd (Join-Path $PSScriptRoot "..\backend")
    python -m pytest tests/test_integration.py -v --tb=long
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Host "`nAll integration tests passed!" -ForegroundColor Green
    } else {
        Write-Host "`nSome integration tests failed." -ForegroundColor Red
    }

    exit $exitCode
} finally {
    Cleanup
}
