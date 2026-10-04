$ErrorActionPreference = 'Stop'

$uvPath = 'C:\tools\uv\uv.exe'

# Verify that required tools are installed
nssm --version
& $uvPath --version

$appDir = "C:\app"
$serviceName = 'MainApplication'

# Logging
$logDir = Join-Path -Path $appDir -ChildPath "logs"
New-Item -Path $logDir -ItemType Directory -ErrorAction Ignore
$stdoutLog = Join-Path -Path $logDir -ChildPath "stdout.log"
$stderrLog = Join-Path -Path $logDir -ChildPath "stderr.log"

# Create new service
$appArgs = @(
  "run",
  "--no-default-groups",
  "fastapi",
  "run",
  "--host", "0.0.0.0"
  # Port is 8000 by default in FastAPI
)
nssm install "$serviceName" "$uvPath" ($appArgs -join ' ')
nssm set "$serviceName" AppDirectory "$appDir"
nssm set "$serviceName" AppStdout "$stdoutLog"
nssm set "$serviceName" AppStderr "$stderrLog"
nssm set "$serviceName" AppRotateFiles 1 # Enable log file rotation
nssm set "$serviceName" AppRotateOnline 1 # Rotate logs while the service is running
nssm set "$serviceName" AppRotateSeconds 86400 # 1 day

# Fix emojis(uvicorn) failing the application start in Windows
nssm set "$serviceName" AppEnvironmentExtra `
  "PYTHONUTF8=1" `
  "PYTHONIOENCODING=utf-8" `
  "UV_PYTHON_INSTALL_DIR=C:\tools\uv-python" `
  "UV_CACHE_DIR=C:\tools\uv-cache" `
  "UV_FROZEN=1" `
  "SE_CACHE_PATH=C:\tools\selenium"

# Start the service
Set-Service -Name $serviceName -StartupType Automatic
nssm start "$serviceName"

# Check if the service started successfully
Start-Sleep -Seconds 5
if ((Get-Service $serviceName).Status -ne 'Running') {
  Get-Content $stderrLog -Tail 50 -ErrorAction Ignore
  throw "Service ${serviceName} failed to start."
}
