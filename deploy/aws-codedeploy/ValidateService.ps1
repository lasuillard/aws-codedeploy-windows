$ErrorActionPreference = 'Continue'

$Uri = "http://localhost:8000"

# Try up to 30 times (about 150 seconds)
$maxRetries = 30
$retryCount = 0
$sleepDuration = 5

Write-Host "Starting health check for $Uri; will retry up to $maxRetries times with $sleepDuration seconds interval."
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
