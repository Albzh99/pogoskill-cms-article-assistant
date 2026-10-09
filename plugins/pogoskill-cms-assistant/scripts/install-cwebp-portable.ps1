$ErrorActionPreference = 'Stop'

$version = '1.6.0'
$packageName = "libwebp-$version-windows-x64"
$toolsRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\tools'))
$target = Join-Path $toolsRoot $packageName
$zipPath = Join-Path $toolsRoot ($packageName + '.zip')
$url = "https://storage.googleapis.com/downloads.webmproject.org/releases/webp/$packageName.zip"

if (Test-Path -LiteralPath $target) {
  throw "Target already exists; refusing to overwrite: $target"
}
[IO.Directory]::CreateDirectory($toolsRoot) | Out-Null

& 'C:\Windows\System32\curl.exe' --fail --location --silent --show-error --output $zipPath $url
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $zipPath -PathType Leaf)) {
  throw 'Official libwebp download failed.'
}

$hash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
Expand-Archive -LiteralPath $zipPath -DestinationPath $toolsRoot
$cwebp = Join-Path $target 'bin\cwebp.exe'
$webpinfo = Join-Path $target 'bin\webpinfo.exe'
if (-not (Test-Path -LiteralPath $cwebp -PathType Leaf) -or -not (Test-Path -LiteralPath $webpinfo -PathType Leaf)) {
  throw 'Downloaded package does not contain the expected cwebp/webpinfo binaries.'
}

$evidence = @(
  "source=$url"
  "sha256=$hash"
  "installed_at=$([DateTimeOffset]::Now.ToString('o'))"
) -join [Environment]::NewLine
[IO.File]::WriteAllText((Join-Path $toolsRoot ($packageName + '.sha256.txt')), $evidence, (New-Object Text.UTF8Encoding($false)))

[pscustomobject]@{ version = $version; cwebp = $cwebp; archive_sha256 = $hash }
