$ErrorActionPreference = 'Stop'

$testRoot = Join-Path ([IO.Path]::GetTempPath()) ('pogoskill-cms-credential-test-' + [Guid]::NewGuid().ToString('N'))
$resolvedTestRoot = [IO.Path]::GetFullPath($testRoot)
$resolvedTempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
if (-not $resolvedTestRoot.StartsWith($resolvedTempRoot, [StringComparison]::OrdinalIgnoreCase)) {
  throw 'Refusing to use a test directory outside the operating-system temp directory.'
}

$script:CmsCredentialFallbackRoot = $resolvedTestRoot
. (Join-Path $PSScriptRoot 'CmsCredential.ps1')

$testKey = 'A' + 'FS' + 'TEST-' + [Guid]::NewGuid().ToString('N')
try {
  $result = Set-CmsStoredApiKey -ApiKey $testKey -SkipCredentialManager
  if (-not $result.FallbackSaved) { throw 'Fallback save did not report success.' }
  if (-not (Test-Path -LiteralPath $script:CmsCredentialFallbackPath -PathType Leaf)) {
    throw 'Fallback credential file was not created.'
  }
  $storedText = [IO.File]::ReadAllText($script:CmsCredentialFallbackPath, [Text.Encoding]::UTF8)
  if ($storedText.Contains($testKey)) { throw 'Fallback credential was stored as plaintext.' }

  $readKey = Get-CmsStoredApiKey -SkipCredentialManager
  if ($readKey -cne $testKey) { throw 'Fallback credential round-trip failed.' }
  Write-Output 'CMS credential fallback test passed.'
}
finally {
  $testKey = $null
  $readKey = $null
  if (
    (Test-Path -LiteralPath $resolvedTestRoot -PathType Container) -and
    $resolvedTestRoot.StartsWith($resolvedTempRoot, [StringComparison]::OrdinalIgnoreCase)
  ) {
    [IO.Directory]::Delete($resolvedTestRoot, $true)
  }
}
