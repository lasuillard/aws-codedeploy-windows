$ErrorActionPreference = 'Stop'

Set-Location C:\app

nssm install MainApplication (Get-Command python).Source -m pipx run uv run --frozen `
    uvicorn `
    main:app `
    --host 0.0.0.0

nssm set MainApplication AppDirectory C:\app
nssm start MainApplication
Start-Sleep 5
nssm status MainApplication
