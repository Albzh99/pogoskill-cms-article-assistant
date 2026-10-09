param(
  [Parameter(Mandatory = $true)][string]$InputHtml,
  [Parameter(Mandatory = $true)][string]$ManifestPath,
  [Parameter(Mandatory = $true)][string]$OutputHtml
)

$ErrorActionPreference = 'Stop'
$inputFile = [IO.Path]::GetFullPath($InputHtml)
$manifestFile = [IO.Path]::GetFullPath($ManifestPath)
$outputFile = [IO.Path]::GetFullPath($OutputHtml)
if ($inputFile -eq $outputFile) { throw 'OutputHtml must be a new file; inspect it before replacing any draft source.' }
if (-not (Test-Path -LiteralPath $inputFile -PathType Leaf)) { throw "HTML not found: $inputFile" }
if (-not (Test-Path -LiteralPath $manifestFile -PathType Leaf)) { throw "Manifest not found: $manifestFile" }

$html = Get-Content -LiteralPath $inputFile -Raw -Encoding UTF8
$manifest = Get-Content -LiteralPath $manifestFile -Raw -Encoding UTF8 | ConvertFrom-Json

foreach ($item in $manifest.items) {
  if ($item.status -ne 'image_published') { throw "Image resource is not published and publicly verified: $($item.image_key), status=$($item.status)" }
  foreach ($required in @('image_key','alt','fallback_public_url','webp_public_url','max_width','site_id')) {
    if ([string]::IsNullOrWhiteSpace([string]$item.$required)) { throw "Manifest field missing for $($item.image_key): $required" }
  }
  $escapedKey = [regex]::Escape([string]$item.image_key)
  $pattern = '(?s)<div class="img-wrap text-center">\s*<!--\s*IMAGE_PENDING(?:(?!-->).)*?image-key:\s*' + $escapedKey + '(?:(?!-->).)*?-->\s*</div>'
  $matches = [regex]::Matches($html, $pattern)
  if ($matches.Count -ne 1) { throw "Expected exactly one placeholder for $($item.image_key), found $($matches.Count)." }

  $alt = [Net.WebUtility]::HtmlEncode([string]$item.alt)
  $webpPublicUrl = [string]$item.webp_public_url
  $fallbackPublicUrl = [string]$item.fallback_public_url
  if ($webpPublicUrl -match 'site\.p\.cms\.afirstsoft\.cn|[?&]attachment=1' -or
      $fallbackPublicUrl -match 'site\.p\.cms\.afirstsoft\.cn|[?&]attachment=1') {
    throw "CMS backend or attachment URL must not enter article HTML: $($item.image_key)"
  }
  $expectedPrefix = if ([int]$item.site_id -eq 324) { 'https://tw.pogoskill.com/images/' } elseif ([int]$item.site_id -eq 286) { 'https://images.pogoskill.com/' } else { throw "Unsupported site_id for $($item.image_key)" }
  if (-not $webpPublicUrl.StartsWith($expectedPrefix) -or -not $fallbackPublicUrl.StartsWith($expectedPrefix)) {
    throw "Public image URL does not match site_id for $($item.image_key)"
  }
  $webpUrl = [Net.WebUtility]::HtmlEncode($webpPublicUrl)
  $fallbackUrl = [Net.WebUtility]::HtmlEncode($fallbackPublicUrl)
  $loadingUrl = if ([int]$item.site_id -eq 324) { 'https://tw.pogoskill.com/images/loading.svg' } else { 'https://images.pogoskill.com/loading.svg' }
  $maxWidth = [int]$item.max_width
  if ($maxWidth -le 0 -or $maxWidth -gt [int]$item.width) { throw "Invalid max_width for $($item.image_key)" }
  $isPhoneScreenshot = ([string]$item.display_mode -eq 'phone-screenshot')
  $isVertical = ([int]$item.height -gt [int]$item.width)
  if ($isPhoneScreenshot -or $isVertical) {
    $maxHeight = if ($item.PSObject.Properties.Name -contains 'max_height' -and [int]$item.max_height -gt 0) {
      [int]$item.max_height
    } else {
      [Math]::Min(520, [int]$item.height)
    }
    if ($maxHeight -le 0 -or $maxHeight -gt [int]$item.height) { throw "Invalid max_height for $($item.image_key)" }
    $displayStyle = "max-height:${maxHeight}px;max-width:100%;width:auto;height:auto;"
  } else {
    $displayStyle = "max-width:${maxWidth}px;width:100%;height:auto;"
  }
  $block = @"
<div class="img-wrap text-center">
  <picture>
    <source class="lozad img-fluid"
            srcset="$loadingUrl"
            data-srcset="$webpUrl"
            type="image/webp">
    <img class="lozad img-fluid"
         src="$loadingUrl"
         data-src="$fallbackUrl"
         alt="$alt"
         style="$displayStyle">
  </picture>
</div>
"@
  $html = [regex]::Replace($html, $pattern, [Text.RegularExpressions.MatchEvaluator]{ param($m) $block }, 1)
}

if ($html -match '<!--\s*IMAGE_PENDING(?:(?!-->).)*?image-key:\s*(?:' + (($manifest.items.image_key | ForEach-Object {[regex]::Escape($_)}) -join '|') + ')') {
  throw 'At least one manifest placeholder remains after replacement.'
}
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($outputFile)) | Out-Null
[IO.File]::WriteAllText($outputFile, $html, (New-Object Text.UTF8Encoding($false)))
[pscustomobject]@{ output = $outputFile; replaced = @($manifest.items).Count }
