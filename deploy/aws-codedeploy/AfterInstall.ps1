# TODO(lasuillard): Some commands are not running; need logs
$ErrorActionPreference = 'Stop'

Set-Location C:\app

# Install pipx
# TODO(lasuillard): Command pipx is not recognized in the current session
#                   Chocolatey Update-SessionEnvironment (refreshenv) also can't help
python -m pip install pipx
python -m pipx ensurepath --force

# Install core utils
python -m pipx install uv aws-annoying

# Install dependencies
python -m pipx run uv python install
python -m pipx run uv sync --frozen
