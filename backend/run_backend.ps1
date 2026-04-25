# Run the FastAPI backend with the correct module path from any location
# Usage: .\run_backend.ps1

$backendDir = Join-Path $PSScriptRoot "backend"

if (-not (Test-Path $backendDir)) {
    Write-Error "Backend directory not found: $backendDir"
    exit 1
}

Push-Location $backendDir

try {
    uvicorn app.main:app --reload
} finally {
    Pop-Location
}
