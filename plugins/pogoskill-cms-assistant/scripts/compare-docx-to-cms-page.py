import argparse
from collections import Counter
import html
import json
import re
import sys
from pathlib import Path


def normalize(text):
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"^(?:H[123]|標題)[:：]", "", text)
    return text


STEP_PREFIX = re.compile(r"^(?:step|步驟|步骤)[：:.]?[0-9０-９]+[：:.、-]?", re.I)
STEP_PREFIX_RAW = re.compile(r"^\s*(?:step|步驟|步骤)\s*[：:.]?[0-9０-９]+\s*[：:.、-]?\s*", re.I)


def step_body(text):
    """Return normalized source step copy without its visual Step N badge."""
    value = normalize(text)
    stripped = STEP_PREFIX.sub("", value, count=1)
    return stripped if stripped != value and stripped else None


def is_step_badge_only(text):
    value = normalize(text)
    return bool(value and STEP_PREFIX.fullmatch(value))


def step_lead(text):
    """Only an explicit short source lead before a colon may become bold."""
    body = STEP_PREFIX_RAW.sub("", text, count=1)
    match = re.match(r"^([^：:]{2,35}[：:])", body)
    return normalize(match.group(1)) if match else None


def step_bold_copy(text):
    return normalize(STEP_PREFIX_RAW.sub("", text, count=1))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("structure_json")
    parser.add_argument("page_json")
    parser.add_argument("--min-ratio", type=float, default=0.0)
    args = parser.parse_args()

    structure = json.loads(Path(args.structure_json).read_text(encoding="utf-8"))
    response = json.loads(Path(args.page_json).read_text(encoding="utf-8"))
    page = response["data"]
    content = page.get("content", "")
    plain = normalize(content)
    content_lines = content.splitlines()
    html_readable = (
        len(content) < 3000
        or (len(content_lines) >= 12 and max(map(len, content_lines)) <= 2400)
    )

    source_text = []
    for block in structure["blocks"]:
        if block["type"] == "paragraph" and block.get("text"):
            value = normalize(block["text"])
            if value:
                source_text.append(value)
        elif block["type"] == "table":
            for row in block["rows"]:
                source_text.extend(normalize(cell) for cell in row if normalize(cell))

    matches = [item for item in source_text if len(item) >= 12 and item in plain]
    comparable = [item for item in source_text if len(item) >= 12]
    missing = [item for item in comparable if item not in plain]
    source_step_blocks = []
    source_step_leads = []
    source_step_bold_spans = []
    blocks = structure["blocks"]
    for index, block in enumerate(blocks):
        if block["type"] != "paragraph" or not block.get("text"):
            continue
        value = step_body(block["text"])
        if value and len(value) >= 6:
            source_step_blocks.append(value)
            source_step_bold_spans.extend(block.get("bold_spans", []))
            if lead := step_lead(block["text"]):
                source_step_leads.append(lead)
            continue
        if is_step_badge_only(block["text"]):
            for following in blocks[index + 1:]:
                if following["type"] != "paragraph" or not following.get("text"):
                    continue
                value = normalize(following["text"])
                if value and len(value) >= 6:
                    source_step_blocks.append(value)
                    source_step_bold_spans.extend(following.get("bold_spans", []))
                    if lead := step_lead(following["text"]):
                        source_step_leads.append(lead)
                break
    missing_step_blocks = [item for item in source_step_blocks if item not in plain]
    rendered_step_bold = Counter(
        normalize(item) for block in re.findall(
            r'<ul\b[^>]*class="[^"]*\bstep-cont\b[^"]*"[^>]*>(.*?)</ul>',
            content, re.I | re.S
        )
        for item in re.findall(r"<label>\s*<strong>(.*?)</strong>", block, re.I | re.S)
    )
    missing_step_bold = []
    for lead in source_step_leads:
        if rendered_step_bold[lead]:
            rendered_step_bold[lead] -= 1
        else:
            missing_step_bold.append(lead)
    source_bold = [step_bold_copy(span) for span in source_step_bold_spans
                   if len(step_bold_copy(span)) >= 2]
    rendered_bold = Counter(normalize(item) for item in re.findall(
        r"<(?:strong|b)\b[^>]*>(.*?)</(?:strong|b)>", content, re.I | re.S
    ))
    missing_source_bold = []
    for span in source_bold:
        matched = next((candidate for candidate in (span, span + "：", span + ":")
                        if rendered_bold[candidate]), None)
        if matched is None:
            missing_source_bold.append(span)
        else:
            rendered_bold[matched] -= 1
    image_urls = list(dict.fromkeys(re.findall(r'(?:src|srcset)="([^"]+)"', content, re.I)))
    headings = [
        normalize(item)
        for item in re.findall(r"<h[23][^>]*>(.*?)</h[23]>", content, re.I | re.S)
    ]
    payload = {
        "page": {key: page.get(key) for key in (
            "id", "subject", "title", "description", "url", "status", "sync_status",
            "version", "author_id", "classify_page_id", "sidebar_module_id", "related_id", "product_id"
        )},
        "source_comparable_blocks": len(comparable),
        "exact_block_matches": len(matches),
        "exact_block_match_ratio": round(len(matches) / len(comparable), 4) if comparable else 0,
        "missing_blocks": missing,
        "source_step_blocks": source_step_blocks,
        "missing_step_blocks": missing_step_blocks,
        "source_step_leads": source_step_leads,
        "missing_step_bold": missing_step_bold,
        "missing_source_bold": missing_source_bold,
        "headings": headings,
        "image_urls": image_urls,
        "html_readable": html_readable,
    }
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    ratio = payload["exact_block_match_ratio"]
    if args.min_ratio and ratio < args.min_ratio:
        print(
            f"Source coverage {ratio:.4f} is below required {args.min_ratio:.4f}",
            file=sys.stderr,
        )
        sys.exit(1)
    if missing_step_blocks:
        print(
            "Guide/operation step wording differs from the DOCX source; "
            "formatting may change, but step copy must remain exact.",
            file=sys.stderr,
        )
        sys.exit(1)
    if missing_step_bold or missing_source_bold:
        print(
            "Source step lead or explicit bold text lost its <strong>/<b> formatting.",
            file=sys.stderr,
        )
        sys.exit(1)
    if not html_readable:
        print("CMS readback content is a compressed HTML chunk.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
