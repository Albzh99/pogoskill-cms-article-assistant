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
  if ($null -eq $contentProperty -or [string]::IsNullOrWhiteSpace([string]$contentProperty.Value)) {
    throw 'Page writes require complete article content.'
  }
  else {
    $content = [string]$contentProperty.Value
    $literalNewlineTokens = @('`r`n', '`n', '`r', '\r\n', '\n', '\r', "‘n", "’n", '&#96;n', '&grave;n')
    foreach ($token in $literalNewlineTokens) {
      if ($content.Contains($token)) {
        throw "HTML content contains a literal newline escape token ($token). Use real line breaks and serialize the JSON payload exactly once."
      }
    }
    if ($content.Length -ge 3000) {
      $lines = $content -split "\r?\n"
      $longest = ($lines | ForEach-Object Length | Measure-Object -Maximum).Maximum
      if ($lines.Count -lt 12 -or $longest -gt 2400) {
        throw 'Article HTML is a compressed chunk; use real line breaks and readable indentation.'
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
  else {
    throw 'PoGoskill package writes only site_id 286 (English) or 324 (Traditional Chinese).'
  }
}

$curlCommand = Get-Command curl.exe -ErrorAction SilentlyContinue | Select-Object -First 1
$curl = if ($curlCommand) { $curlCommand.Source } else { 'C:\Windows\System32\curl.exe' }
if (-not (Test-Path -LiteralPath $curl -PathType Leaf)) { throw 'curl.exe was not found.' }

if ($Path -in @('/cms/page/add', '/cms/page/update')) {
  $classifyResponsePath = Join-Path $env:TEMP ('pogoskill-classify-' + [guid]::NewGuid().ToString('N') + '.json')
  $classifyBodyPath = Join-Path $env:TEMP ('pogoskill-classify-body-' + [guid]::NewGuid().ToString('N') + '.json')
  try {
    [IO.File]::WriteAllText($classifyBodyPath, ('{"site_id":' + [int]$payload.site_id + '}'), (New-Object Text.UTF8Encoding($false)))
    & $curl -sS --fail-with-body --connect-timeout 20 --max-time 90 -X POST 'https://gw.afirstsoft.com/cms/classify/displayclassifylist' -H ("X-API-KEY: $apiKey") -H 'Accept: application/json' -H 'Content-Type: application/json; charset=utf-8' --data-binary ('@' + $classifyBodyPath) -o $classifyResponsePath
    if ($LASTEXITCODE -ne 0) { throw "Classification query transport error: curl exit=$LASTEXITCODE" }
    $classifyResponse = [IO.File]::ReadAllText($classifyResponsePath, [Text.Encoding]::UTF8) | ConvertFrom-Json
    if ([int]$classifyResponse.code -ne 0 -or [string]::IsNullOrWhiteSpace([string]$classifyResponse.request_id)) {
      throw "Classification query failed: code=$($classifyResponse.code), request_id=$($classifyResponse.request_id)"
    }
    $chosen = @($classifyResponse.data.list | Where-Object { [string]$_.id -eq [string]$payload.classify_page_id })
    if ($chosen.Count -ne 1) { throw 'classify_page_id does not belong to the live target-site classification list.' }
    $category = $chosen[0]
    if ([string]$category.status -ne '1') { throw 'Selected classification is disabled.' }
    if ($payload.classify_id -and [string]$payload.classify_id -ne [string]$category.classify_id) {
      throw 'classify_id and classify_page_id refer to different classifications.'
    }
    $directory = ([string]$category.dir).Trim('/')
    $articleUrl = ([string]$payload.url).TrimStart('/')
    if (-not $directory -or -not $articleUrl.StartsWith($directory + '/', [StringComparison]::Ordinal)) {
      throw 'Article URL must start with the selected classification directory.'
    }
    $topic = @($payload.subject, $payload.title, $payload.keywords, $payload.seo_keywords, $payload.url) -join ' '
    if ($topic -match '(?i)pikmin|皮克敏') {
      if ($directory -ne 'pikmin-bloom' -or -not $articleUrl.StartsWith('pikmin-bloom/', [StringComparison]::Ordinal)) {
        throw 'Pikmin Bloom articles must use the live pikmin-bloom classification and URL, not game-app.'
      }
    }
  }
  finally {
    Remove-Item -LiteralPath $classifyResponsePath, $classifyBodyPath -Force -ErrorAction SilentlyContinue
  }
}

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
