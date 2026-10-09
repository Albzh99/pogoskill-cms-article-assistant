param(
  [Parameter(Mandatory = $true)][string]$ManifestPath,
  [string]$CwebpPath
)

$ErrorActionPreference = 'Stop'
$manifestFile = [IO.Path]::GetFullPath($ManifestPath)
if (-not (Test-Path -LiteralPath $manifestFile -PathType Leaf)) { throw "Manifest not found: $manifestFile" }
$manifest = Get-Content -LiteralPath $manifestFile -Raw -Encoding UTF8 | ConvertFrom-Json

if ([string]::IsNullOrWhiteSpace($CwebpPath)) {
  $relativeTool = Join-Path $PSScriptRoot '..\..\..\tools\libwebp-1.6.0-windows-x64\bin\cwebp.exe'
  $command = Get-Command cwebp -ErrorAction SilentlyContinue
  if (Test-Path -LiteralPath $relativeTool) { $CwebpPath = $relativeTool }
  elseif ($command) { $CwebpPath = $command.Source }
  else { throw 'cwebp is unavailable. Restore the bundled tools directory or install cwebp on PATH.' }
}
$CwebpPath = [IO.Path]::GetFullPath($CwebpPath)
if (-not (Test-Path -LiteralPath $CwebpPath -PathType Leaf)) { throw "cwebp not found: $CwebpPath" }
$webpInfoPath = Join-Path ([IO.Path]::GetDirectoryName($CwebpPath)) 'webpinfo.exe'
if (-not (Test-Path -LiteralPath $webpInfoPath -PathType Leaf)) { throw "webpinfo not found beside cwebp: $webpInfoPath" }

foreach ($item in $manifest.items) {
  if (-not (Test-Path -LiteralPath $item.fallback_path -PathType Leaf)) { throw "Fallback missing: $($item.fallback_path)" }
  if ([IO.Path]::GetExtension($item.fallback_path).ToLowerInvariant() -eq '.png') {
    & $CwebpPath -quiet -lossless -z 9 -metadata none $item.fallback_path -o $item.webp_path
  }
  else {
    & $CwebpPath -quiet -q 90 -m 6 -metadata none $item.fallback_path -o $item.webp_path
  }
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $item.webp_path -PathType Leaf)) {
    throw "WebP conversion failed for $($item.fallback_name)"
  }
  if ((Get-Item -LiteralPath $item.webp_path).Length -le 0) { throw "WebP output is empty: $($item.webp_path)" }
  $info = (& $webpInfoPath -summary $item.webp_path 2>&1) -join "`n"
  if ($LASTEXITCODE -ne 0 -or $info -notmatch 'No error detected\.') { throw "WebP validation failed for $($item.webp_name)" }
  $widthMatch = [regex]::Match($info, '(?m)^\s*Width:\s*(\d+)\s*$')
  $heightMatch = [regex]::Match($info, '(?m)^\s*Height:\s*(\d+)\s*$')
  if (-not $widthMatch.Success -or -not $heightMatch.Success) { throw "Unable to read WebP dimensions for $($item.webp_name)" }
  if ([int]$widthMatch.Groups[1].Value -ne [int]$item.width -or [int]$heightMatch.Groups[1].Value -ne [int]$item.height) {
    throw "WebP dimensions differ from fallback for $($item.image_key)"
  }
  $item | Add-Member -NotePropertyName webp_sha256 -NotePropertyValue ((Get-FileHash -LiteralPath $item.webp_path -Algorithm SHA256).Hash.ToLowerInvariant()) -Force
  $item | Add-Member -NotePropertyName webp_width -NotePropertyValue ([int]$widthMatch.Groups[1].Value) -Force
  $item | Add-Member -NotePropertyName webp_height -NotePropertyValue ([int]$heightMatch.Groups[1].Value) -Force
  $item.status = 'converted'
}

$manifest | Add-Member -NotePropertyName converted_at -NotePropertyValue ([DateTimeOffset]::Now.ToString('o')) -Force
[IO.File]::WriteAllText($manifestFile, ($manifest | ConvertTo-Json -Depth 14), (New-Object Text.UTF8Encoding($false)))
[pscustomobject]@{ manifest = $manifestFile; converted = @($manifest.items).Count; cwebp = $CwebpPath }
