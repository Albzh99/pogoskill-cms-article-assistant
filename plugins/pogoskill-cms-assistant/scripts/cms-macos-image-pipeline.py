"""macOS image-manifest pipeline. Never generates or publishes article pages.

The upload and publish commands require --execute. All mutations checkpoint the
manifest and preserve CMS responses so an interrupted run can be investigated.
"""

import argparse
import hashlib
import html
import importlib.util
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request


HERE = Path(__file__).resolve().parent
PREFIX = {324: "https://tw.pogoskill.com/images/", 286: "https://images.pogoskill.com/"}
CMS_PATH = re.compile(r"^[a-z0-9/_-]*$")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def load_script(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), HERE / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, manifest):
    Path(path).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def pillow():
    try:
        from PIL import Image, features
    except ImportError as exc:
        raise RuntimeError("Pillow is required on macOS: python3 -m pip install Pillow") from exc
    if not features.check("webp"):
        raise RuntimeError("This Pillow installation has no WebP encoder")
    return Image


def extract(docx, output, slug):
    if not SLUG.fullmatch(slug):
        raise ValueError("Article slug must be lowercase English words separated by hyphens")
    output = Path(output).resolve()
    manifest_path = output / "image-manifest.json"
    if manifest_path.exists():
        raise FileExistsError("Existing image manifest must not be overwritten")
    source = load_script("extract-docx-media.py").extract(docx, output / "source")
    Image = pillow()
    items = []
    for row in source["images"]:
        original = Path(row["extracted_path"])
        ext = ".jpg" if original.suffix.lower() == ".jpeg" else original.suffix.lower()
        if ext not in {".png", ".jpg"}:
            raise ValueError(f"Unsupported fallback image: {original.name}")
        basename = f"{slug}-{row['occurrence']:02d}"
        fallback = output / f"{basename}{ext}"
        webp = output / f"{basename}.webp"
        if fallback.exists() or webp.exists():
            raise FileExistsError(f"Existing image would be overwritten: {basename}")
        with Image.open(original) as image:
            image.load()
            width, height = image.size
        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid image dimensions: {original}")
        fallback.write_bytes(original.read_bytes())
        items.append({"image_key": f"img-{row['occurrence']:02d}", "source_entry": row["source_entry"],
            "relationship_id": row["relationship_id"], "source_sha256": row["source_sha256"],
            "fallback_path": str(fallback), "fallback_name": fallback.name, "fallback_ext": ext,
            "webp_path": str(webp), "webp_name": webp.name, "width": width, "height": height,
            "alt": "", "max_width": min(width, 850), "status": "extracted"})
    if not items:
        raise ValueError("DOCX has no embedded JPG/PNG image")
    manifest = {"schema_version": 1, "article_slug": slug, "source_docx": str(Path(docx).resolve()),
                "extracted_at": now(), "items": items}
    save(manifest_path, manifest)
    return manifest_path


def convert(manifest_path):
    Image = pillow()
    manifest = read(manifest_path)
    for item in manifest["items"]:
        fallback = Path(item["fallback_path"])
        webp = Path(item["webp_path"])
        if not fallback.is_file():
            raise FileNotFoundError(fallback)
        if webp.exists() and item.get("status") != "converted":
            raise FileExistsError(f"Untracked WebP must not be overwritten: {webp}")
        with Image.open(fallback) as image:
            image.load()
            if image.size != (item["width"], item["height"]):
                raise ValueError(f"Fallback dimensions changed: {fallback}")
            if fallback.suffix.lower() == ".png":
                image.save(webp, "WEBP", lossless=True, method=6)
            else:
                image.convert("RGB").save(webp, "WEBP", quality=90, method=6)
        with Image.open(webp) as checked:
            checked.load()
            if checked.format != "WEBP" or checked.size != (item["width"], item["height"]):
                raise ValueError(f"WebP validation failed: {webp}")
        item.update(webp_sha256=hashlib.sha256(webp.read_bytes()).hexdigest(),
                    webp_width=item["width"], webp_height=item["height"], status="converted")
        save(manifest_path, manifest)
    manifest["converted_at"] = now()
    save(manifest_path, manifest)
    return manifest


def http_readable(url):
    if not isinstance(url, str) or not url.startswith("https://"):
        return False
    try:
        with request.urlopen(request.Request(url, headers={"Range": "bytes=0-0"}), timeout=30) as response:
            return response.status in (200, 206)
    except (error.HTTPError, error.URLError, TimeoutError):
        return False


def list_files(cms, site_id, cms_path):
    response = cms.request_json("/cms/picture/list", {"site_id": site_id, "path": cms_path, "type": "file"})
    rows = response.get("data", {}).get("list", [])
    files = [child for row in rows for child in row.get("fileChildren", [])]
    return response, {entry.get("name"): entry for entry in files}


def public_url(uploaded, listed, prefix, width, height):
    for candidate in (uploaded.get("url"), listed.get("online")):
        if isinstance(candidate, str) and candidate.startswith(prefix) and "attachment=1" not in candidate:
            return candidate if re.search(r"[?&]w=", candidate) else f"{candidate}{'&' if '?' in candidate else '?'}w={width}&h={height}"
    raise ValueError(f"CMS did not return a valid public URL for {uploaded.get('name')}")


def find_evidence(evidence_dir, item):
    for path in sorted(evidence_dir.glob("picture-upload-*-response.json"), reverse=True):
        try:
            response = read(path)
            data = response.get("data", {})
            names = {row.get("name") for row in data.get("list", [])}
            if response.get("code") == 0 and data.get("publish_id") and {item["fallback_name"], item["webp_name"]} <= names:
                return path, response
        except (ValueError, TypeError, OSError):
            continue
    return None, None


def upload(manifest_path, site_id, cms_path, cms=None):
    if site_id not in PREFIX or not CMS_PATH.fullmatch(cms_path):
        raise ValueError("Unsupported PoGoskill site or invalid CMS image path")
    cms = cms or load_script("cms-macos.py")
    manifest = read(manifest_path)
    evidence_dir = Path(manifest_path).resolve().parent / "cms-evidence"
    evidence_dir.mkdir(exist_ok=True)
    cms.request_json("/cms/picture/dirs", {"site_id": site_id, "path": cms_path, "tree": 0})
    for item in manifest["items"]:
        if item.get("status") == "image_published":
            continue
        if not item.get("alt") or item.get("status") not in {"converted", "reused_existing", "uploaded_pending_publish", "image_publish_submitted"}:
            raise ValueError(f"Image is not converted or ALT is missing: {item['image_key']}")
        for field in ("fallback", "webp"):
            path = Path(item[f"{field}_path"])
            if not path.is_file() or not 0 < path.stat().st_size <= 30 * 1024 * 1024:
                raise ValueError(f"Missing or oversized image: {path}")
        response, files = list_files(cms, site_id, cms_path)
        fallback, webp = files.get(item["fallback_name"]), files.get(item["webp_name"])
        if bool(fallback) != bool(webp):
            raise ValueError(f"Only one image format exists: {item['image_key']}")
        upload_response = None
        evidence_path = None
        if fallback and webp:
            for entry in (fallback, webp):
                if (entry.get("w"), entry.get("h")) != (item["width"], item["height"]):
                    raise ValueError(f"Existing image dimensions conflict: {entry.get('name')}")
            evidence_path, upload_response = find_evidence(evidence_dir, item)
            if not evidence_path and item.get("upload_evidence_path"):
                evidence_path = Path(item["upload_evidence_path"])
                upload_response = read(evidence_path)
            status = "reused_existing"
        else:
            body, content_type = cms.multipart_image_body(site_id, cms_path, [item["fallback_path"], item["webp_path"]])
            upload_response = cms.cms_post("/cms/picture/upload", body, content_type)
            evidence_path = evidence_dir / f"picture-upload-{item['image_key']}-{int(time.time() * 1000)}-response.json"
            save(evidence_path, upload_response)
            data = upload_response.get("data", {})
            names = {row.get("name") for row in data.get("list", [])}
            if data.get("total") != 2 or data.get("err_name_files") or {item["fallback_name"], item["webp_name"]} != names:
                raise ValueError(f"CMS did not accept the complete image pair: {item['image_key']}")
            response, files = list_files(cms, site_id, cms_path)
            fallback, webp = files.get(item["fallback_name"]), files.get(item["webp_name"])
            if not fallback or not webp:
                raise ValueError(f"Uploaded pair is missing from picture/list: {item['image_key']}")
            status = "uploaded_pending_publish"
        uploaded = {row["name"]: row for row in upload_response.get("data", {}).get("list", [])} if upload_response else {}
        for label, listed in (("fallback", fallback), ("webp", webp)):
            candidate = uploaded.get(item[f"{label}_name"], listed)
            item[f"{label}_upload_url"] = listed.get("upload") or candidate.get("upload")
            if not http_readable(item[f"{label}_upload_url"]):
                raise ValueError(f"CMS upload URL is not readable: {item[f'{label}_name']}")
            item[f"{label}_public_url"] = public_url(candidate, listed, PREFIX[site_id], item["width"], item["height"])
        item.update(site_id=site_id, cms_path=cms_path, list_request_id=response["request_id"],
                    status=status, fallback_url_readable=True, webp_url_readable=True)
        if upload_response:
            item.update(upload_request_id=upload_response["request_id"],
                        publish_id=upload_response["data"]["publish_id"], upload_evidence_path=str(evidence_path))
        manifest["upload_last_checkpoint"] = item["image_key"]
        save(manifest_path, manifest)
    return manifest


def publish(manifest_path, cms=None, readable=http_readable, sleep=time.sleep,
            wait_seconds=300, interval=5, clock=time.monotonic, verify_only=False):
    if not 1 <= wait_seconds <= 600:
        raise ValueError("wait_seconds must be between 1 and 600")
    manifest = read(manifest_path)
    pending = []
    changed = False
    for item in manifest["items"]:
        urls = (item.get("fallback_public_url"), item.get("webp_public_url"))
        if not all(urls):
            raise ValueError(f"Missing public URLs: {item['image_key']}")
        if all(map(readable, urls)):
            item["status"] = "image_published"
            changed = True
        elif item.get("status") == "image_publish_submitted":
            continue
        elif item.get("status") in {"uploaded_pending_publish", "reused_existing"}:
            if verify_only:
                raise ValueError(f"Image has no recorded publication: {item['image_key']}; verification mode cannot publish it")
            if not item.get("upload_request_id") or not item.get("publish_id"):
                raise ValueError(f"Original image upload evidence is missing: {item['image_key']}")
            pending.append(item)
        else:
            raise ValueError(f"Image is not ready to publish: {item['image_key']}")
    if changed:
        save(manifest_path, manifest)
    if pending:
        cms = cms or load_script("cms-macos.py")
        ids = sorted({int(item["publish_id"]) for item in pending})
        result = cms.request_json("/cms/pagepublish/publish", {"ids": ids,
            "description": "Publish CMS image resources only; no article page publication"}, allow_image_publish=True)
        data = result.get("data", {})
        succeeded = {int(row["id"]) for row in data.get("success", [])}
        if data.get("failed") or not set(ids) <= succeeded:
            raise ValueError(f"Image resource publication incomplete: request_id={result['request_id']}")
        for item in pending:
            item.update(status="image_publish_submitted", image_publish_request_id=result["request_id"],
                        image_publish_submitted_at=now())
        save(manifest_path, manifest)
    remaining = [item for item in manifest["items"] if item["status"] == "image_publish_submitted"]
    deadline = clock() + wait_seconds
    next_progress = clock()
    while remaining:
        not_ready = []
        for item in remaining:
            if readable(item["fallback_public_url"]) and readable(item["webp_public_url"]):
                item.update(status="image_published", image_public_verified_at=now())
                save(manifest_path, manifest)
            else:
                not_ready.append(item)
        remaining = not_ready
        if not remaining:
            break
        seconds_left = deadline - clock()
        if seconds_left <= 0:
            keys = ", ".join(item["image_key"] for item in remaining)
            raise RuntimeError(f"Public image URLs still syncing after {wait_seconds}s: {keys}; "
                               "keep image_publish_submitted and retry verification only")
        if clock() >= next_progress:
            print(f"Waiting for public image sync: {len(remaining)} pair(s); no upload or publication retry.", flush=True)
            next_progress = clock() + 30
        sleep(min(interval, seconds_left))
    return manifest


def apply(manifest_path, input_html, output_html):
    source, target = Path(input_html).resolve(), Path(output_html).resolve()
    if source == target or target.exists():
        raise ValueError("Output HTML must be a new file; never overwrite the source")
    manifest = read(manifest_path)
    body = source.read_text(encoding="utf-8")
    for item in manifest["items"]:
        if item.get("status") != "image_published":
            raise ValueError(f"Image is not published: {item['image_key']}")
        site_id = item.get("site_id")
        prefix = PREFIX.get(site_id)
        if not prefix or not item.get("alt"):
            raise ValueError(f"Missing site or ALT: {item['image_key']}")
        urls = [item.get("webp_public_url"), item.get("fallback_public_url")]
        if any(not isinstance(url, str) or not url.startswith(prefix) or "attachment=1" in url for url in urls):
            raise ValueError(f"Invalid public URL: {item['image_key']}")
        pattern = re.compile(r'<div class="img-wrap text-center">\s*<!--\s*IMAGE_PENDING(?:(?!-->).)*?image-key:\s*'
                             + re.escape(item["image_key"]) + r'(?:(?!-->).)*?-->\s*</div>', re.S)
        if len(pattern.findall(body)) != 1:
            raise ValueError(f"Expected exactly one placeholder: {item['image_key']}")
        vertical = item.get("display_mode") == "phone-screenshot" or item["height"] > item["width"]
        if vertical:
            height = min(int(item.get("max_height") or 520), item["height"])
            style = f"max-height:{height}px;max-width:100%;width:auto;height:auto;"
        else:
            width = int(item["max_width"])
            if not 0 < width <= item["width"]:
                raise ValueError(f"Invalid max_width: {item['image_key']}")
            style = f"max-width:{width}px;width:100%;height:auto;"
        loading = prefix + "loading.svg"
        block = (f'<div class="img-wrap text-center">\n  <picture>\n'
                 f'    <source class="lozad img-fluid" srcset="{loading}" data-srcset="{html.escape(urls[0], quote=True)}" type="image/webp">\n'
                 f'    <img class="lozad img-fluid" src="{loading}" data-src="{html.escape(urls[1], quote=True)}" '
                 f'alt="{html.escape(item["alt"], quote=True)}" style="{style}">\n  </picture>\n</div>')
        body = pattern.sub(lambda _: block, body, count=1)
    if "IMAGE_PENDING" in body:
        raise ValueError("Unfilled image placeholder remains")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    a = commands.add_parser("extract")
    a.add_argument("docx")
    a.add_argument("--output-dir", required=True)
    a.add_argument("--article-slug", required=True)
    a = commands.add_parser("convert")
    a.add_argument("--manifest", required=True)
    for name in ("upload", "publish", "verify-public"):
        a = commands.add_parser(name)
        a.add_argument("--manifest", required=True)
        if name != "verify-public":
            a.add_argument("--execute", action="store_true", required=True)
        if name in ("publish", "verify-public"):
            a.add_argument("--max-wait-seconds", type=int, default=300)
        if name == "upload":
            a.add_argument("--site-id", type=int, required=True)
            a.add_argument("--cms-path", required=True)
    a = commands.add_parser("apply")
    a.add_argument("--manifest", required=True)
    a.add_argument("--input-html", required=True)
    a.add_argument("--output-html", required=True)
    args = parser.parse_args()
    if sys.platform != "darwin":
        raise RuntimeError("This entry point is for macOS; Windows uses the existing PowerShell scripts")
    if args.command == "extract":
        print(extract(args.docx, args.output_dir, args.article_slug))
    elif args.command == "convert":
        print(json.dumps({"converted": len(convert(args.manifest)["items"])}, ensure_ascii=False))
    elif args.command == "upload":
        print(json.dumps({"items": len(upload(args.manifest, args.site_id, args.cms_path)["items"])}, ensure_ascii=False))
    elif args.command == "publish":
        print(json.dumps({"published_images": sum(i["status"] == "image_published" for i in publish(
            args.manifest, wait_seconds=args.max_wait_seconds)["items"])}))
    elif args.command == "verify-public":
        print(json.dumps({"published_images": sum(i["status"] == "image_published" for i in publish(
            args.manifest, wait_seconds=args.max_wait_seconds, verify_only=True)["items"])}))
    else:
        print(apply(args.manifest, args.input_html, args.output_html))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
