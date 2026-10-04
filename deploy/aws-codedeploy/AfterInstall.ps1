$ErrorActionPreference = 'Stop'

# Use machine-level fixed paths for uv and related tools
$env:UV_INSTALL_DIR = 'C:\tools\uv'
$env:UV_NO_MODIFY_PATH = '1'
$env:UV_PYTHON_INSTALL_DIR = 'C:\tools\uv-python'
$env:UV_CACHE_DIR = 'C:\tools\uv-cache'
$env:UV_FROZEN = '1'
$env:SE_CACHE_PATH = 'C:\tools\selenium'

# Install uv
Write-Output 'Installing uv...'
Invoke-RestMethod "https://astral.sh/uv/install.ps1" | Invoke-Expression

# Verify uv installation
$uvPath = "C:\tools\uv\uv.exe"
& $uvPath --version

# Navigate to app directory
New-Item -ItemType Directory -Path "C:\\app" -Force | Out-Null
Set-Location "C:\\app"

# Install Python and dependencies
& $uvPath python install
& $uvPath sync --no-default-groups

# Pre-download the webdriver
& $uvPath run --no-default-groups python .\scripts\pre-download-webdriver.py
