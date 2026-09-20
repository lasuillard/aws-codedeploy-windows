$ErrorActionPreference = 'Continue'

$Uri = "http://localhost:8000"

# Try up to 100 times (about 300 seconds)
$maxRetries = 100
$retryCount = 0
$sleepDuration = 5

while ($retryCount -lt $maxRetries) {
    Write-Host "Attempting health check... ($($retryCount + 1) / $maxRetries)"
    try {
        $response = Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "Health check passed."
            exit 0
        } else {
            Write-Host "Health check failed with status code: $($response.StatusCode)"
        }
    } catch {
        Write-Host "Health check failed with exception: $_, retrying in $sleepDuration seconds..."
    }

    Start-Sleep -Seconds $sleepDuration
    $retryCount++
}

Write-Host "Health check failed after $maxRetries attempts."
exit 1
