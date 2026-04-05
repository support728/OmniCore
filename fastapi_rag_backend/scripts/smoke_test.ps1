$ErrorActionPreference = "Stop"

$ApiBaseUrl = if ($env:OMNICORE_API_BASE_URL) { $env:OMNICORE_API_BASE_URL } else { "http://localhost:8002" }
$ApiBaseUrl = $ApiBaseUrl.TrimEnd('/')

Write-Host "Checking health endpoint..."
$health = Invoke-RestMethod -Method Get -Uri "$ApiBaseUrl/health"
if ($health.status -ne "ok") {
    Write-Error "Health endpoint not OK"
}

$username = "pilotuser$([int](Get-Random -Minimum 1000 -Maximum 9999))"
$password = "PilotUser!2026"

Write-Host "Registering test user: $username"
$registerBody = @{ username = $username; password = $password; display_name = "Pilot User" } | ConvertTo-Json
$session = Invoke-RestMethod -Method Post -Uri "$ApiBaseUrl/api/auth/register" -ContentType "application/json" -Body $registerBody
$token = $session.access_token

if (-not $token) {
    Write-Error "No access token returned"
}

$headers = @{ Authorization = "Bearer $token" }

Write-Host "Creating first goal..."
$goalBody = @{ title = "Validate onboarding"; description = "First real-user journey"; priority_weight = 1.2 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$ApiBaseUrl/api/goals" -ContentType "application/json" -Body $goalBody -Headers $headers | Out-Null

Write-Host "Fetching dashboard..."
$dashboard = Invoke-RestMethod -Method Get -Uri "$ApiBaseUrl/api/dashboard" -Headers $headers

Write-Host "Smoke test passed."
Write-Host "Top goals count: $($dashboard.top_goals.Count)"
Write-Host "User id: $($dashboard.user_id)"
