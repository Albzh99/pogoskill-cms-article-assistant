$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'CmsCredential.ps1')

$apiKey = $null
try {
  $apiKey = Get-CmsStoredApiKey
  if ([string]::IsNullOrWhiteSpace($apiKey)) {
    Write-Error 'CMS API key is not stored in either protected local storage or Windows Credential Manager.'
    exit 1
  }
  Write-Output 'CMS API key is available. The secret value was not displayed.'
}
finally {
  $apiKey = $null
}
