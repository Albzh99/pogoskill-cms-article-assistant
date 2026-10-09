param(
  [Parameter(Mandatory = $true)][string]$ResponsePath
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'CmsProductMapping.ps1')

$path = [IO.Path]::GetFullPath($ResponsePath)
if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "CMS page/info response not found: $path" }
try { $response = Get-Content -Raw -Encoding UTF8 -LiteralPath $path | ConvertFrom-Json }
catch { throw "CMS page/info response is not valid JSON: $path" }

if ([int]$response.code -ne 0) { throw "CMS page/info failed: code=$($response.code), request_id=$($response.request_id), msg=$($response.msg)" }
$pageProperty = $response.data.PSObject.Properties['page']
$page = if ($null -ne $pageProperty) { $pageProperty.Value } else { $response.data }
$siteId = [string]$page.site_id
if ($siteId -eq '286') { $ids = Assert-PoGoskillEnglishProductSelection -ProductId $page.product_id }
elseif ($siteId -eq '324') { $ids = Assert-PoGoskillTwProductSelection -ProductId $page.product_id }
else { throw "Unsupported PoGoskill site_id: $siteId" }
[pscustomobject]@{
  ok = $true
  page_id = [string]$page.id
  site_id = $siteId
  product_id = $ids
  products = @('PoGoskill', 'PoGoskill(Mac)')
  request_id = [string]$response.request_id
} | ConvertTo-Json -Depth 5
