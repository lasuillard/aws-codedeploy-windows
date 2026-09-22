$ErrorActionPreference = 'Stop'

# NOTE: Reload the PATH environment variable; CodeDeploy may not have the updated PATH for installed tools
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Verify that required tools are installed
nssm --version
uv --version

$appDir = "C:\app"
$serviceName = 'MainApplication'

# Logging
$logDir = Join-Path -Path "$appDir" -ChildPath "logs"
New-Item -Path "$logDir" -ItemType Directory -ErrorAction Ignore
$stdoutLog = Join-Path -Path "$logDir" -ChildPath "stdout.log"
$stderrLog = Join-Path -Path "$logDir" -ChildPath "stderr.log"

# Create new service
$uvPath = (Get-Command uv -ErrorAction Stop).Source
$appArgs = @(
  "run",
  "--frozen",
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
nssm set "$serviceName" AppEnvironmentExtra "PYTHONUTF8=1" "PYTHONIOENCODING=utf-8"

# Start the service
Set-Service -Name "$serviceName" -StartupType Automatic
nssm start "$serviceName"
