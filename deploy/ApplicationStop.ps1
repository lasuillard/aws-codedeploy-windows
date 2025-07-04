$ErrorActionPreference = 'Continue'

nssm stop MainApplication
nssm remove MainApplication confirm
