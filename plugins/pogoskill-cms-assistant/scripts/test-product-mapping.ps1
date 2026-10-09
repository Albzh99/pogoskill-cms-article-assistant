$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'CmsProductMapping.ps1')

$valid = [pscustomobject]@{ product_id = @('4987', '4988') }
Assert-PoGoskillEnglishProductSelection -ProductId $valid.product_id -RequireCanonicalPayload | Out-Null
$validTw = [pscustomobject]@{ product_id = @('6333', '6332') }
Assert-PoGoskillTwProductSelection -ProductId $validTw.product_id -RequireCanonicalPayload | Out-Null

$invalidCases = @(
  [pscustomobject]@{ Value = @(4987, 4988); Canonical = $true },
  [pscustomobject]@{ Value = @('4988', '4987'); Canonical = $true },
  [pscustomobject]@{ Value = @('7959', '7960'); Canonical = $false },
  [pscustomobject]@{ Value = '["4987","4988"]'; Canonical = $true }
)

foreach ($case in $invalidCases) {
  $failed = $false
  try {
    if ($case.Canonical) {
      Assert-PoGoskillEnglishProductSelection -ProductId $case.Value -RequireCanonicalPayload | Out-Null
    }
    else {
      Assert-PoGoskillEnglishProductSelection -ProductId $case.Value | Out-Null
    }
  }
  catch { $failed = $true }
  if (-not $failed) { throw "Expected invalid product selection to fail: $($case.Value | ConvertTo-Json -Compress)" }
}

$twFailed = $false
try { Assert-PoGoskillTwProductSelection -ProductId @('7925', '7926') | Out-Null }
catch { $twFailed = $true }
if (-not $twFailed) { throw 'DCC download PIDs 7925/7926 must not be accepted as Traditional Chinese CMS product IDs.' }

'Product mapping tests passed.'
