param(
  [Parameter(Mandatory = $true)][string]$DocxPath,
  [Parameter(Mandatory = $true)][string]$OutputDirectory,
  [Parameter(Mandatory = $true)][ValidatePattern('^[a-z0-9-]+$')][string]$ArticleSlug
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.Drawing

function Read-ZipText([IO.Compression.ZipArchive]$Zip, [string]$Name) {
  $entry = $Zip.GetEntry($Name)
  if (-not $entry) { throw "DOCX entry missing: $Name" }
  $reader = New-Object IO.StreamReader($entry.Open(), [Text.Encoding]::UTF8)
  try { return $reader.ReadToEnd() } finally { $reader.Dispose() }
}

function Get-ImageSize([byte[]]$Bytes) {
  $stream = New-Object IO.MemoryStream(,$Bytes)
  try {
    $image = [Drawing.Image]::FromStream($stream, $false, $true)
    try { return @{ width = $image.Width; height = $image.Height } }
    finally { $image.Dispose() }
  }
  finally { $stream.Dispose() }
}

$docx = [IO.Path]::GetFullPath($DocxPath)
$output = [IO.Path]::GetFullPath($OutputDirectory)
if (-not (Test-Path -LiteralPath $docx -PathType Leaf)) { throw "DOCX not found: $docx" }
if ([IO.Path]::GetExtension($docx).ToLowerInvariant() -ne '.docx') { throw 'DocxPath must end in .docx.' }
[IO.Directory]::CreateDirectory($output) | Out-Null

$zip = [IO.Compression.ZipFile]::OpenRead($docx)
try {
  [xml]$document = Read-ZipText $zip 'word/document.xml'
  [xml]$rels = Read-ZipText $zip 'word/_rels/document.xml.rels'

  $docNs = New-Object Xml.XmlNamespaceManager($document.NameTable)
  $docNs.AddNamespace('a', 'http://schemas.openxmlformats.org/drawingml/2006/main')
  $docNs.AddNamespace('r', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships')

  $relMap = @{}
  foreach ($rel in $rels.Relationships.Relationship) {
    $relMap[[string]$rel.Id] = [string]$rel.Target
  }

  $items = @()
  $index = 0
  foreach ($blip in $document.SelectNodes('//a:blip[@r:embed]', $docNs)) {
    $rid = $blip.GetAttribute('embed', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships')
    $target = $relMap[$rid]
    if ([string]::IsNullOrWhiteSpace($target)) { throw "Missing relationship target for $rid" }
    $entryName = ('word/' + $target.TrimStart('/')).Replace('\', '/')
    $entry = $zip.GetEntry($entryName)
    if (-not $entry) { throw "Referenced image is missing: $entryName" }

    $sourceExt = [IO.Path]::GetExtension($entryName).ToLowerInvariant()
    if ($sourceExt -notin @('.jpg', '.jpeg', '.png')) {
      throw "Unsupported article image format $sourceExt at $entryName; only JPG/PNG are accepted."
    }
    $fallbackExt = if ($sourceExt -eq '.jpeg') { '.jpg' } else { $sourceExt }

    $memory = New-Object IO.MemoryStream
    $input = $entry.Open()
    try { $input.CopyTo($memory) } finally { $input.Dispose() }
    $bytes = $memory.ToArray()
    $memory.Dispose()
    if ($bytes.Length -eq 0) { throw "Referenced image is empty: $entryName" }

    $sha256 = [Security.Cryptography.SHA256]::Create()
    try {
      $sha = ([BitConverter]::ToString($sha256.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    }
    finally { $sha256.Dispose() }
    $index++
    # Keep the checksum in the manifest for duplicate detection, never in the public filename.
    $baseName = '{0}-{1:d2}' -f $ArticleSlug, $index
    $fallbackName = $baseName + $fallbackExt
    $fallbackPath = Join-Path $output $fallbackName
    [IO.File]::WriteAllBytes($fallbackPath, $bytes)
    $size = Get-ImageSize $bytes

    $items += [ordered]@{
      image_key = 'img-{0:d2}' -f $index
      source_entry = $entryName
      relationship_id = $rid
      source_sha256 = $sha
      fallback_path = $fallbackPath
      fallback_name = $fallbackName
      fallback_ext = $fallbackExt
      webp_path = (Join-Path $output ($baseName + '.webp'))
      webp_name = $baseName + '.webp'
      width = [int]$size.width
      height = [int]$size.height
      alt = ''
      max_width = [Math]::Min(850, [int]$size.width)
      status = 'extracted'
    }
  }

  if ($items.Count -eq 0) { throw 'No JPG or PNG images are referenced by word/document.xml.' }
  $manifest = [ordered]@{
    schema_version = 1
    article_slug = $ArticleSlug
    source_docx = $docx
    extracted_at = [DateTimeOffset]::Now.ToString('o')
    items = $items
  }
  $manifestPath = Join-Path $output 'image-manifest.json'
  [IO.File]::WriteAllText($manifestPath, ($manifest | ConvertTo-Json -Depth 12), (New-Object Text.UTF8Encoding($false)))
  [pscustomobject]@{ manifest = $manifestPath; count = $items.Count }
}
finally {
  $zip.Dispose()
}
