import argparse
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path


def normalize_source_entry(value):
    value = str(value or "").replace("\\", "/").lstrip("/")
    while value.startswith("../"):
        value = value[3:]
    if value.startswith("word/"):
        return value
    return f"word/{value}"


def source_occurrences(structure):
    occurrences = []
    for block_index, block in enumerate(structure.get("blocks", [])):
        if block.get("type") != "paragraph":
            continue
        for image_index, target in enumerate(block.get("images", [])):
            occurrences.append({
                "occurrence": len(occurrences) + 1,
                "block_index": block_index,
                "image_index": image_index,
                "source_entry": normalize_source_entry(target),
            })
    return occurrences


GUIDE_FILENAME = re.compile(r"(?<![A-Za-z0-9_-])([A-Za-z0-9][A-Za-z0-9_-]*\.(?:jpe?g|png|webp))(?![A-Za-z0-9_-])", re.I)


def named_image_references(structure):
    names = []
    for block in structure.get("blocks", []):
        texts = []
        if block.get("type") == "paragraph":
            texts.append(block.get("text", ""))
        elif block.get("type") == "table":
            texts.extend(cell for row in block.get("rows", []) for cell in row)
        for text in texts:
            for match in GUIDE_FILENAME.finditer(str(text or "")):
                name = match.group(1)
                if name.lower() not in {item.lower() for item in names}:
                    names.append(name)
    return names


def extract_content(path):
    raw = Path(path).read_text(encoding="utf-8-sig")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if isinstance(payload, dict):
        if isinstance(payload.get("data"), dict) and isinstance(payload["data"].get("content"), str):
            return payload["data"]["content"]
        if isinstance(payload.get("content"), str):
            return payload["content"]
    raise ValueError("HTML input JSON does not contain data.content or content")


def validate(structure, manifest, content):
    expected = source_occurrences(structure)
    named_references = named_image_references(structure)
    items = manifest.get("items", [])
    errors = []

    keys = [str(item.get("image_key") or "") for item in items]
    duplicate_keys = sorted(key for key, count in Counter(keys).items() if key and count > 1)
    missing_keys = [index + 1 for index, key in enumerate(keys) if not key]
    if duplicate_keys:
        errors.append(f"duplicate image_key values: {', '.join(duplicate_keys)}")
    if missing_keys:
        errors.append(f"manifest items without image_key: {missing_keys}")

    expected_entries = [item["source_entry"] for item in expected]
    manifest_entries = [normalize_source_entry(item.get("source_entry")) for item in items]
    expected_counter = Counter(expected_entries)
    manifest_counter = Counter(manifest_entries)
    missing_source_entries = list((expected_counter - manifest_counter).elements())
    extra_manifest_entries = list((manifest_counter - expected_counter).elements())
    if missing_source_entries:
        errors.append("source image occurrences missing from manifest: " + ", ".join(missing_source_entries))
    if extra_manifest_entries:
        errors.append("manifest image occurrences not present in source: " + ", ".join(extra_manifest_entries))
    if len(items) != len(expected):
        errors.append(f"source/manifest image count differs: {len(expected)} != {len(items)}")

    unpublished = []
    missing_html_image_keys = []
    missing_urls = []
    decoded_content = html.unescape(content)
    for item in items:
        key = str(item.get("image_key") or "<missing-key>")
        if item.get("status") != "image_published":
            unpublished.append(key)
        item_missing = []
        for field in ("fallback_public_url", "webp_public_url"):
            url = str(item.get(field) or "")
            if not url or url not in decoded_content:
                item_missing.append(field)
                if url:
                    missing_urls.append(url)
        if item_missing:
            missing_html_image_keys.append(key)
    if unpublished:
        errors.append("image resources are not published: " + ", ".join(unpublished))
    if missing_html_image_keys:
        errors.append("manifest images missing from final HTML: " + ", ".join(missing_html_image_keys))
    if "IMAGE_PENDING" in content:
        errors.append("final HTML still contains IMAGE_PENDING")

    missing_named_images = []
    for name in named_references:
        stem, extension = name.rsplit(".", 1)
        if name.lower() not in decoded_content.lower():
            missing_named_images.append(name)
            continue
        if extension.lower() in {"jpg", "jpeg", "png"} and f"{stem}.webp".lower() not in decoded_content.lower():
            missing_named_images.append(f"{stem}.webp")
    if missing_named_images:
        errors.append("DOCX-named images missing from final HTML: " + ", ".join(missing_named_images))

    payload = {
        "source_embedded_image_count": len(expected),
        "manifest_image_count": len(items),
        "html_manifest_image_count": len(items) - len(missing_html_image_keys),
        "source_occurrences": expected,
        "source_named_image_count": len(named_references),
        "source_named_images": named_references,
        "missing_source_entries": missing_source_entries,
        "extra_manifest_entries": extra_manifest_entries,
        "duplicate_image_keys": duplicate_keys,
        "unpublished_image_keys": unpublished,
        "missing_html_image_keys": missing_html_image_keys,
        "missing_public_urls": missing_urls,
        "missing_named_images": missing_named_images,
        "pending_placeholder_count": content.count("IMAGE_PENDING"),
        "errors": errors,
        "pass": not errors,
    }
    return payload


def main():
    parser = argparse.ArgumentParser(
        description="Block CMS draft writes when a DOCX image occurrence is absent from the manifest or final HTML."
    )
    parser.add_argument("structure_json")
    parser.add_argument("image_manifest_json")
    parser.add_argument("html_or_page_json")
    parser.add_argument("--out")
    args = parser.parse_args()

    structure = json.loads(Path(args.structure_json).read_text(encoding="utf-8-sig"))
    manifest = json.loads(Path(args.image_manifest_json).read_text(encoding="utf-8-sig"))
    content = extract_content(args.html_or_page_json)
    result = validate(structure, manifest, content)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)
    if args.out:
        Path(args.out).write_text(rendered + "\n", encoding="utf-8")
    if not result["pass"]:
        print("Image coverage validation failed; do not call page/add or page/update.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
