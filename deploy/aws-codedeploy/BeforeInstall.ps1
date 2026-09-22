$ErrorActionPreference = 'Continue'

# Application service
$serviceName = 'MainApplication'

# Stop existing service if it is running
$service = Get-Service -Name "$serviceName" -ErrorAction SilentlyContinue
if (-Not $service) {
  Write-Output "Service ${serviceName} does not exist."
  return
}

# Gracefully stop the service if it is running (up to 30 seconds)
$elapsedTime = 0
$gracePeriodSec = 30
$checkIntervalSec = 3

if ($service.Status -eq 'Running') {
  nssm stop "$serviceName"

  while ($elapsedTime -lt $gracePeriodSec -and $service.Status -eq 'Running') {
    $processes = Get-Process -Name 'python' -ErrorAction SilentlyContinue | Where-Object { $_.Path -like 'C:\app\*' }
    if (-Not $processes) {
      Write-Output "All application processes shut down successfully."
      break
    }
    Write-Output "Waiting for application processes to shut down..."
    Start-Sleep -Seconds $checkIntervalSec
    $elapsedTime += $checkIntervalSec
  }

  $remainingProcesses = Get-Process -Name 'python' -ErrorAction SilentlyContinue | Where-Path { $_.Path -like 'C:\app\*' }
  if ($remainingProcesses) {
    Write-Output "Exceeded maximum retries for stopping service ${serviceName}. Terminating remaining python processes."
    $remainingProcesses | Stop-Process -Force
  }
}

Write-Output "Removing service ${serviceName}..."
nssm remove "${serviceName}" confirm
