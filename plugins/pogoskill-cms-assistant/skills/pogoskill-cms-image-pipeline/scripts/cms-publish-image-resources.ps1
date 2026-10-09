param(
  [Parameter(Mandatory = $true)][string]$ManifestPath,
  [switch]$Execute
)

$ErrorActionPreference = 'Stop'
if (-not $Execute) { throw 'Dry run only. Re-run with -Execute only for image resource publication; this script never publishes an article page.' }

$manifestFile = [IO.Path]::GetFullPath($ManifestPath)
if (-not (Test-Path -LiteralPath $manifestFile -PathType Leaf)) { throw "Manifest not found: $manifestFile" }
$manifest = Get-Content -LiteralPath $manifestFile -Raw -Encoding UTF8 | ConvertFrom-Json

$credentialScript = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\scripts\CmsCredential.ps1'))
if (-not (Test-Path -LiteralPath $credentialScript -PathType Leaf)) { throw 'Plugin credential helper was not found.' }
. $credentialScript
$apiKey = Get-CmsStoredApiKey
if ([string]::IsNullOrWhiteSpace($apiKey)) { throw 'Stored CMS credential not found.' }
$curlCommand = Get-Command curl.exe -ErrorAction SilentlyContinue | Select-Object -First 1
$curl = if ($curlCommand) { $curlCommand.Source } else { 'C:\Windows\System32\curl.exe' }
if (-not (Test-Path -LiteralPath $curl -PathType Leaf)) { throw 'curl.exe was not found.' }

function Save-Manifest {
  [IO.File]::WriteAllText($manifestFile, ($manifest | ConvertTo-Json -Depth 18), (New-Object Text.UTF8Encoding($false)))
}

function Invoke-CmsJson([string]$Path, [hashtable]$Body) {
  $requestBody = Join-Path $env:TEMP ('cms-image-publish-' + [guid]::NewGuid().ToString('N') + '.json')
  $responseBody = Join-Path $env:TEMP ('cms-image-publish-response-' + [guid]::NewGuid().ToString('N') + '.json')
  try {
    [IO.File]::WriteAllText($requestBody, ($Body | ConvertTo-Json -Depth 10 -Compress), (New-Object Text.UTF8Encoding($false)))
    @("X-API-KEY: $apiKey", 'Accept: application/json', 'Content-Type: application/json; charset=utf-8') |
      & $curl -k -sS -X POST ('https://gw.afirstsoft.com' + $Path) -H '@-' --data-binary ('@' + $requestBody) -o $responseBody
    if ($LASTEXITCODE -ne 0) { throw "Transport error on ${Path}: curl exit=$LASTEXITCODE" }
    return [IO.File]::ReadAllText($responseBody, [Text.Encoding]::UTF8) | ConvertFrom-Json
  }
  finally {
    Remove-Item -LiteralPath $requestBody -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $responseBody -Force -ErrorAction SilentlyContinue
  }
}

function Test-PublicUrl([string]$Url) {
  if ([string]::IsNullOrWhiteSpace($Url) -or $Url -notmatch '^https://') { return $false }
  $status = & $curl -k -sS -L --range '0-0' -o NUL -w '%{http_code}' --connect-timeout 10 --max-time 30 $Url
  return ($LASTEXITCODE -eq 0 -and $status -in @('200', '206'))
}

function Test-PublicPair([object]$Item) {
  return (Test-PublicUrl ([string]$Item.fallback_public_url)) -and (Test-PublicUrl ([string]$Item.webp_public_url))
}

try {
  $publishItems = @()
  $submittedItems = @()
  foreach ($item in $manifest.items) {
    foreach ($required in @('image_key', 'fallback_public_url', 'webp_public_url')) {
      if ([string]::IsNullOrWhiteSpace([string]$item.$required)) { throw "Manifest field missing for $($item.image_key): $required" }
    }
    if (Test-PublicPair $item) {
      $item.status = 'image_published'
      continue
    }
    if ($item.status -eq 'image_publish_submitted') {
      $submittedItems += $item
      continue
    }
    if ($item.status -notin @('uploaded_pending_publish', 'reused_existing')) {
      throw "Image is not ready for image-resource publication: $($item.image_key), status=$($item.status)"
    }
    if ([int]$item.publish_id -le 0 -or [string]::IsNullOrWhiteSpace([string]$item.upload_request_id)) {
      throw "Image publish_id/upload evidence is missing for $($item.image_key). Recover the original picture/upload response; never use an article page ID."
    }
    $publishItems += $item
  }

  if ($publishItems.Count -gt 0) {
    $ids = @($publishItems | ForEach-Object { [int]$_.publish_id } | Select-Object -Unique)
    $publishResponse = Invoke-CmsJson '/cms/pagepublish/publish' @{
      ids = $ids
      description = 'Publish CMS article image resources to cloud storage; no article page publication'
    }
    if ($publishResponse.code -ne 0) {
      throw "Image resource publish failed: code=$($publishResponse.code), request_id=$($publishResponse.request_id), msg=$($publishResponse.msg)"
    }
    $failed = @($publishResponse.data.failed)
    $successIds = @($publishResponse.data.success | ForEach-Object { [int]$_.id })
    $missingIds = @($ids | Where-Object { $_ -notin $successIds })
    if ($failed.Count -ne 0 -or $missingIds.Count -ne 0) {
      throw "Image resource publish was partial: request_id=$($publishResponse.request_id), failed=$($failed.Count), missing=$($missingIds -join ',')"
    }
    foreach ($item in $publishItems) {
      $item | Add-Member -NotePropertyName image_publish_request_id -NotePropertyValue $publishResponse.request_id -Force
      $item | Add-Member -NotePropertyName image_publish_submitted_at -NotePropertyValue ([DateTimeOffset]::Now.ToString('o')) -Force
      $item.status = 'image_publish_submitted'
      $submittedItems += $item
    }
    Save-Manifest
  }

  foreach ($item in $submittedItems) {
    $readable = $false
    for ($attempt = 1; $attempt -le 10; $attempt++) {
      if (Test-PublicPair $item) { $readable = $true; break }
      if ($attempt -lt 10) { Start-Sleep -Seconds 3 }
    }
    if (-not $readable) {
      Save-Manifest
      throw "Image publish succeeded but public URLs are not readable yet for $($item.image_key). Do not publish the same ID again; retry only this verification step."
    }
    $item | Add-Member -NotePropertyName image_public_verified_at -NotePropertyValue ([DateTimeOffset]::Now.ToString('o')) -Force
    $item.status = 'image_published'
  }

  $manifest | Add-Member -NotePropertyName image_resources_checked_at -NotePropertyValue ([DateTimeOffset]::Now.ToString('o')) -Force
  Save-Manifest
  [pscustomobject]@{
    manifest = $manifestFile
    image_publish_ids = @($publishItems | ForEach-Object { [int]$_.publish_id } | Select-Object -Unique)
    published_images = @($manifest.items | Where-Object status -eq 'image_published').Count
    article_page_published = $false
  }
}
finally {
  $apiKey = $null
}
