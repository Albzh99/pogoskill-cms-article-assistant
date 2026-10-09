param(
  [Parameter(Mandatory = $true)][ValidatePattern('^/cms/[a-z0-9/_-]+$')][string]$Path,
  [Parameter(Mandatory = $true)][string]$BodyPath,
  [string]$OutputPath
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'CmsCredential.ps1')
. (Join-Path $PSScriptRoot 'CmsProductMapping.ps1')
$apiKey = [string](Get-CmsStoredApiKey)
if ([string]::IsNullOrWhiteSpace($apiKey)) { throw 'Stored CMS credential not found. Run cms-save-api-key.ps1 first.' }

$body = [IO.Path]::GetFullPath($BodyPath)
if (-not (Test-Path -LiteralPath $body -PathType Leaf)) { throw "JSON body not found: $body" }
try { $payload = Get-Content -Raw -Encoding UTF8 -LiteralPath $body | ConvertFrom-Json }
catch { throw "Body is not valid JSON: $body" }

if ($Path -in @('/cms/page/add', '/cms/page/update')) {
  $contentProperty = $payload.PSObject.Properties['content']
  if ($null -ne $contentProperty) {
    $content = [string]$contentProperty.Value
    $literalNewlineTokens = @('`r`n', '`n', '`r', '\r\n', '\n', '\r', "‘n", "’n", '&#96;n', '&grave;n')
    foreach ($token in $literalNewlineTokens) {
      if ($content.Contains($token)) {
        throw "HTML content contains a literal newline escape token ($token). Use real line breaks and serialize the JSON payload exactly once."
      }
    }
  }

  if ([string]$payload.site_id -eq '286') {
    $productProperty = $payload.PSObject.Properties['product_id']
    if ($null -eq $productProperty) {
      throw 'English site page writes require product_id ["4987","4988"].'
    }
    Assert-PoGoskillEnglishProductSelection -ProductId $productProperty.Value -RequireCanonicalPayload | Out-Null
  }
  elseif ([string]$payload.site_id -eq '324') {
    $productProperty = $payload.PSObject.Properties['product_id']
    if ($null -eq $productProperty) {
      throw 'Traditional Chinese site page writes require product_id ["6333","6332"].'
    }
    Assert-PoGoskillTwProductSelection -ProductId $productProperty.Value -RequireCanonicalPayload | Out-Null
  }
}

$curlCommand = Get-Command curl.exe -ErrorAction SilentlyContinue | Select-Object -First 1
$curl = if ($curlCommand) { $curlCommand.Source } else { 'C:\Windows\System32\curl.exe' }
if (-not (Test-Path -LiteralPath $curl -PathType Leaf)) { throw 'curl.exe was not found.' }

$responsePath = Join-Path $env:TEMP ('pogoskill-cms-response-' + [guid]::NewGuid().ToString('N') + '.json')
try {
  & $curl -sS --fail-with-body --connect-timeout 20 --max-time 90 -X POST `
    ('https://gw.afirstsoft.com' + $Path) `
    -H ("X-API-KEY: $apiKey") `
    -H 'Accept: application/json' `
    -H 'Content-Type: application/json; charset=utf-8' `
    --data-binary ('@' + $body) -o $responsePath
  if ($LASTEXITCODE -ne 0) { throw "CMS transport error on ${Path}: curl exit=$LASTEXITCODE" }
  $raw = [IO.File]::ReadAllText($responsePath, [Text.Encoding]::UTF8)
  $response = $raw | ConvertFrom-Json
  if ($null -eq $response.code -or [int]$response.code -ne 0) {
    throw "CMS business error on ${Path}: code=$($response.code), request_id=$($response.request_id), msg=$($response.msg)"
  }
  if ($OutputPath) {
    $resolvedOutput = [IO.Path]::GetFullPath($OutputPath)
    [IO.File]::WriteAllText($resolvedOutput, ($response | ConvertTo-Json -Depth 80), (New-Object Text.UTF8Encoding($false)))
  }
  $response | ConvertTo-Json -Depth 80
}
finally {
  $apiKey = $null
  Remove-Item -LiteralPath $responsePath -Force -ErrorAction SilentlyContinue
}
