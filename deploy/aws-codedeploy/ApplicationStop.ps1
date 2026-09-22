$ErrorActionPreference = 'Continue'

nssm --version

$serviceName = 'MainApplication'
$service = Get-Service -Name "$serviceName" -ErrorAction SilentlyContinue

if ($service) {
  nssm stop "$serviceName"
  nssm remove "$serviceName" confirm
}
