"""Check source image occurrences against a site-specific image manifest and HTML."""

import argparse
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path


def normalize_entry(value):
    value = str(value or "").replace("\\", "/").lstrip("/")
    return value if value.startswith("word/") else "word/" + value


def html_content(path):
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
    raise ValueError("HTML JSON must contain content or data.content")


def required_urls(item):
    if isinstance(item.get("html_urls"), list):
        return item["html_urls"]
    return [url for url in (item.get("fallback_public_url"), item.get("webp_public_url")) if url]


def check(structure, manifest, content):
    expected = [normalize_entry(entry)
                for block in structure.get("blocks", [])
                for entry in block.get("images", [])]
    items = manifest.get("items", [])
    entries = [normalize_entry(item.get("source_entry")) for item in items]
    missing_source = list((Counter(expected) - Counter(entries)).elements())
    extra_manifest = list((Counter(entries) - Counter(expected)).elements())
    errors = []
    if missing_source:
        errors.append("source image occurrence absent from manifest")
    if extra_manifest:
        errors.append("manifest image absent from source")
    keys = [item.get("image_key") for item in items]
    if any(not isinstance(key, str) or not key for key in keys) or len(keys) != len(set(keys)):
        errors.append("image_key values must be unique and nonempty")
    unpublished = [item.get("image_key") for item in items if item.get("status") != "image_published"]
    if unpublished:
        errors.append("image resources have not been published and verified")
    decoded = html.unescape(content)
    image_markup = "\n".join(re.findall(r"<(?:img|source)\b[^>]*>", decoded, re.I | re.S))
    missing_html = []
    url_occurrences = Counter(
        url for item in items for url in required_urls(item)
        if isinstance(url, str) and url.startswith("https://")
    )
    for item in items:
        urls = required_urls(item)
        if not isinstance(urls, list) or not urls or any(
            not isinstance(url, str) or not url.startswith("https://") or url not in image_markup for url in urls
        ):
            missing_html.append(item.get("image_key"))
    for url, required_count in url_occurrences.items():
        if image_markup.count(url) < required_count:
            for item in items:
                if url in required_urls(item) and item.get("image_key") not in missing_html:
                    missing_html.append(item.get("image_key"))
    if missing_html:
        errors.append("manifest image URL absent from HTML")
    if "IMAGE_PENDING" in content:
        errors.append("IMAGE_PENDING remains in HTML")
    return {
        "pass": not errors,
        "source_image_occurrences": len(expected),
        "manifest_items": len(items),
        "html_items": len(items) - len(missing_html),
        "missing_source_entries": missing_source,
        "extra_manifest_entries": extra_manifest,
        "missing_html_image_keys": missing_html,
        "unpublished_image_keys": unpublished,
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("structure_json")
    parser.add_argument("site_image_manifest_json")
    parser.add_argument("html_or_page_info_json")
    args = parser.parse_args()
    structure = json.loads(Path(args.structure_json).read_text(encoding="utf-8-sig"))
    manifest = json.loads(Path(args.site_image_manifest_json).read_text(encoding="utf-8-sig"))
    result = check(structure, manifest, html_content(args.html_or_page_info_json))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["pass"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
