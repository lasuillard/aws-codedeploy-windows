$ErrorActionPreference = 'Stop'

Set-Location C:\app

# Install pipx
python -m pip install pipx
python -m pipx ensurepath --force

# Install core utils
python -m pipx install uv aws-annoying

# Install dependencies
python -m pipx run uv python install
python -m pipx run uv sync --frozen
