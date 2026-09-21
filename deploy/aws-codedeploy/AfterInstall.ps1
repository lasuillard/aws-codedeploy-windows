$ErrorActionPreference = 'Stop'

# Install uv
Write-Output 'Installing uv...'
Invoke-RestMethod "https://astral.sh/uv/install.ps1" | Invoke-Expression

$uvPath = "$env:USERPROFILE\.local\bin"
if (-not ($env:Path -like "*$uvPath*")) {
  $env:PATH = "$uvPath;$env:PATH"
  Write-Output "Added $uvPath to PATH"
}

# Verify uv installation
uv --version

# Navigate to app directory
New-Item -ItemType Directory -Path "C:\\app" -Force | Out-Null
Set-Location "C:\\app"

# Install Python and dependencies
uv python install
uv sync --frozen
