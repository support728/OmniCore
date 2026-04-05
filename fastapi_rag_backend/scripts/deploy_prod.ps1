Param(
    [string]$EnvFile = ".env",
    [string]$ComposeFile = "docker-compose.prod.yml",
    [string]$ApiBaseUrl = $(if ($env:OMNICORE_API_BASE_URL) { $env:OMNICORE_API_BASE_URL } else { "http://localhost:8002" })
)

$ErrorActionPreference = "Stop"
$ApiBaseUrl = $ApiBaseUrl.TrimEnd('/')

if (-not (Test-Path $EnvFile)) {
    Write-Error "Missing env file: $EnvFile"
}

if (-not (Test-Path $ComposeFile)) {
    Write-Error "Missing compose file: $ComposeFile"
}

Write-Host "[1/4] Building and starting production services..."
docker compose -f $ComposeFile --env-file $EnvFile up -d --build

Write-Host "[2/4] Waiting for API health endpoint..."
$healthy = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 2
    try {
        $resp = Invoke-RestMethod -Method Get -Uri "$ApiBaseUrl/health" -TimeoutSec 5
        if ($resp.status -eq "ok") {
            $healthy = $true
            break
        }
    } catch {
        # retry
    }
}

if (-not $healthy) {
    Write-Error "API health check failed after 60 seconds."
}

Write-Host "[3/4] Service status"
docker compose -f $ComposeFile ps

Write-Host "[4/4] Deployment complete."
Write-Host "API: $ApiBaseUrl"
Write-Host "Settings: $ApiBaseUrl/settings"
