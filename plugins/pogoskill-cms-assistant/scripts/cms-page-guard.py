"""Preflight checks shared by PoGoskill's Windows and macOS page writers."""

import argparse
import json
import re
from pathlib import Path


PRODUCTS = {286: ["4987", "4988"], 324: ["6333", "6332"]}


def readable_html_errors(content):
    if not isinstance(content, str) or not content.strip():
        return ["article content is empty"]
    errors = []
    if len(content) >= 3000:
        lines = content.splitlines()
        if len(lines) < 12 or max(map(len, lines)) > 2400:
            errors.append("article HTML is a compressed chunk; use real line breaks and readable indentation")
    if re.search(r"`(?:r`n|n|r)|\\(?:r\\n|n|r)|[‘’]n(?=\s|<)", content):
        errors.append("article HTML contains visible escaped-newline text")
    return errors


def payload_errors(payload):
    if not isinstance(payload, dict):
        return ["page payload must be a JSON object"]
    site_id = payload.get("site_id")
    if type(site_id) is not int or site_id not in PRODUCTS:
        return ["PoGoskill package writes only site_id 286 (English) or 324 (Traditional Chinese)"]
    errors = readable_html_errors(payload.get("content"))
    if payload.get("product_id") != PRODUCTS[site_id]:
        errors.append(f"site_id {site_id} requires canonical product_id {PRODUCTS[site_id]}")
    return errors


def classification_errors(payload, response):
    if not isinstance(response, dict) or response.get("code") != 0 or not response.get("request_id"):
        return ["classification query lacks successful code and request_id"]
    data = response.get("data")
    records = data.get("list") if isinstance(data, dict) else None
    if not isinstance(records, list):
        return ["classification response has no data.list"]
    chosen_id = str(payload.get("classify_page_id") or "")
    record = next((item for item in records if isinstance(item, dict) and str(item.get("id")) == chosen_id), None)
    if record is None:
        return ["classify_page_id does not belong to the live target-site classification list"]
    errors = []
    if str(record.get("status")) != "1":
        errors.append("selected classification is disabled")
    own_id = payload.get("classify_id")
    if own_id not in (None, "", 0) and str(own_id) != str(record.get("classify_id")):
        errors.append("classify_id and classify_page_id refer to different classifications")
    directory = str(record.get("dir") or "").strip("/")
    url = str(payload.get("url") or "").lstrip("/")
    if not directory or not url.startswith(directory + "/"):
        errors.append("article URL must start with the selected classification directory")
    topic = " ".join(str(payload.get(key) or "") for key in
                     ("subject", "title", "keywords", "seo_keywords", "url")).lower()
    if "pikmin" in topic or "皮克敏" in topic:
        if directory != "pikmin-bloom":
            errors.append("Pikmin Bloom articles must use the live pikmin-bloom classification, not game-app")
        if not url.startswith("pikmin-bloom/"):
            errors.append("Pikmin Bloom article URL must start with pikmin-bloom/")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("payload_json")
    parser.add_argument("--classify-response", required=True)
    parser.add_argument("--page-info")
    args = parser.parse_args()
    payload = json.loads(Path(args.payload_json).read_text(encoding="utf-8-sig"))
    response = json.loads(Path(args.classify_response).read_text(encoding="utf-8-sig"))
    errors = payload_errors(payload) + classification_errors(payload, response)
    if args.page_info:
        info = json.loads(Path(args.page_info).read_text(encoding="utf-8-sig"))
        page = info.get("data", {})
        if isinstance(page, dict) and isinstance(page.get("info"), dict):
            page = page["info"]
        if info.get("code") != 0 or not info.get("request_id"):
            errors.append("page/info readback lacks successful code and request_id")
        else:
            for key in ("site_id", "classify_id", "classify_page_id", "url", "content"):
                if key == "classify_id" and payload.get(key) in (None, "", 0):
                    continue
                if page.get(key) != payload.get(key):
                    errors.append(f"page/info {key} differs from submitted draft")
            errors.extend(readable_html_errors(page.get("content")))
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
