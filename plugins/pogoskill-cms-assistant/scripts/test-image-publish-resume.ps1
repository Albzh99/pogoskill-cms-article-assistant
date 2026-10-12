$ErrorActionPreference = 'Stop'
$publisher = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\skills\pogoskill-cms-image-pipeline\scripts\cms-publish-image-resources.ps1'))
$tempParent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$testRoot = Join-Path $tempParent ('pogoskill-image-resume-test-' + [guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($testRoot) | Out-Null
try {
  $manifestPath = Join-Path $testRoot 'manifest.json'
  $fixture = @{
    items = @(@{
      image_key = 'img-01'
      status = 'image_publish_submitted'
      fallback_public_url = 'https://127.0.0.1:1/a.png'
      webp_public_url = 'https://127.0.0.1:1/a.webp'
      publish_id = 42
      upload_request_id = 'upload-test'
      image_publish_request_id = 'publish-test'
    })
  }
  [IO.File]::WriteAllText($manifestPath, ($fixture | ConvertTo-Json -Depth 8), [Text.Encoding]::UTF8)
  try {
    & $publisher -ManifestPath $manifestPath -VerifyOnly -MaxWaitSeconds 1
    throw 'Expected a verification timeout for unreachable URLs.'
  }
  catch {
    if ($_.Exception.Message -notmatch 'still syncing') { throw }
  }
  $saved = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($saved.items[0].status -ne 'image_publish_submitted') { throw 'Verification timeout lost the publication checkpoint.' }

  $saved.items[0].status = 'uploaded_pending_publish'
  [IO.File]::WriteAllText($manifestPath, ($saved | ConvertTo-Json -Depth 8), [Text.Encoding]::UTF8)
  try {
    & $publisher -ManifestPath $manifestPath -VerifyOnly -MaxWaitSeconds 1
    throw 'Verification mode must not publish an unsubmitted image.'
  }
  catch {
    if ($_.Exception.Message -notmatch 'Verification mode will not publish') { throw }
  }
  Write-Output 'Image verification resume tests passed.'
}
finally {
  $resolved = [IO.Path]::GetFullPath($testRoot)
  if (-not $resolved.StartsWith($tempParent, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Test cleanup target escaped the temporary directory.'
  }
  [IO.Directory]::Delete($resolved, $true)
}
