Set-StrictMode -Version Latest

function ConvertTo-CmsProductIdList {
  param([Parameter(Mandatory = $true)]$Value)

  $normalized = $Value
  if ($Value -is [string]) {
    $text = $Value.Trim()
    if ($text.StartsWith('[')) {
      try { $normalized = $text | ConvertFrom-Json }
      catch { throw "product_id contains invalid JSON: $text" }
    }
    elseif ($text.Contains(',')) { $normalized = $text.Split(',') }
    else { $normalized = @($text) }
  }

  return @($normalized | ForEach-Object { ([string]$_).Trim() } | Where-Object { $_ })
}

function Assert-PoGoskillEnglishProductSelection {
  param(
    [Parameter(Mandatory = $true)]$ProductId,
    [switch]$RequireCanonicalPayload
  )

  $expected = @('4987', '4988')
  $actual = @(ConvertTo-CmsProductIdList -Value $ProductId)
  $actualSorted = @($actual | Sort-Object -Unique)
  $expectedSorted = @($expected | Sort-Object)
  if (($actualSorted.Count -ne 2) -or (($actualSorted -join ',') -ne ($expectedSorted -join ','))) {
    throw "English site product_id must contain exactly PoGoskill 4987 and PoGoskill(Mac) 4988; received: $($actual -join ', ')"
  }

  if ($RequireCanonicalPayload) {
    if ($ProductId -is [string] -or $ProductId -isnot [System.Collections.IEnumerable]) {
      throw 'English page write product_id must be a JSON array of strings: ["4987","4988"].'
    }
    foreach ($item in @($ProductId)) {
      if ($item -isnot [string]) {
        throw 'English page write product_id must use string IDs, not numeric IDs: ["4987","4988"].'
      }
    }
    if (($actual -join ',') -ne '4987,4988') {
      throw 'English page write product_id must use canonical order: ["4987","4988"].'
    }
  }

  return $actual
}

function Assert-PoGoskillTwProductSelection {
  param(
    [Parameter(Mandatory = $true)]$ProductId,
    [switch]$RequireCanonicalPayload
  )

  $actual = @(ConvertTo-CmsProductIdList -Value $ProductId)
  $actualSorted = @($actual | Sort-Object -Unique)
  if (($actualSorted.Count -ne 2) -or (($actualSorted -join ',') -ne '6332,6333')) {
    throw "Traditional Chinese site product_id must contain exactly PoGoskill 6333 and PoGoskill(Mac) 6332; received: $($actual -join ', ')"
  }
  if ($RequireCanonicalPayload) {
    if ($ProductId -is [string] -or $ProductId -isnot [System.Collections.IEnumerable]) {
      throw 'Traditional Chinese page write product_id must be a JSON array of strings: ["6333","6332"].'
    }
    foreach ($item in @($ProductId)) {
      if ($item -isnot [string]) { throw 'Traditional Chinese page write product_id must use string IDs: ["6333","6332"].' }
    }
    if (($actual -join ',') -ne '6333,6332') {
      throw 'Traditional Chinese page write product_id must use canonical order: ["6333","6332"].'
    }
  }
  return $actual
}
