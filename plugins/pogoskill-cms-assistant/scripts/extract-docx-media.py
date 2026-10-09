"""Extract every inline DOCX image occurrence in document order on Windows or macOS."""

import argparse
import hashlib
import json
import posixpath
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}


def extract(docx_path, output_dir):
    docx_path = Path(docx_path)
    output_dir = Path(output_dir)
    if not docx_path.is_file() or docx_path.suffix.lower() != ".docx":
        raise ValueError("An existing DOCX is required")
    output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(docx_path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
        relroot = ET.fromstring(archive.read("word/_rels/document.xml.rels"))
        rels = {node.get("Id"): node.get("Target") for node in relroot.findall("pr:Relationship", NS)}
        entries = []
        for index, blip in enumerate(root.findall(".//a:blip", NS), 1):
            rel_id = blip.get("{%s}embed" % NS["r"])
            target = rels.get(rel_id)
            if not target:
                raise ValueError(f"Image relationship missing: {rel_id}")
            entry = (posixpath.normpath(target.lstrip("/")) if target.startswith("/")
                     else posixpath.normpath(posixpath.join("word", target)))
            if not entry.startswith("word/media/"):
                raise ValueError(f"Unexpected image target: {entry}")
            raw = archive.read(entry)
            extension = Path(entry).suffix.lower()
            if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
                raise ValueError(f"Unsupported inline image format: {entry}")
            dest = output_dir / f"source-{index:02d}{extension}"
            if dest.exists():
                raise FileExistsError(f"Existing extracted image would be overwritten: {dest}")
            dest.write_bytes(raw)
            entries.append({"occurrence": index, "relationship_id": rel_id, "source_entry": entry,
                "source_sha256": hashlib.sha256(raw).hexdigest(), "extracted_path": str(dest)})
    return {"source": str(docx_path), "image_occurrences": len(entries), "images": entries}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("docx")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    manifest = extract(args.docx, args.output_dir)
    Path(args.manifest).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"image_occurrences": manifest["image_occurrences"], "manifest": args.manifest}, ensure_ascii=False))


if __name__ == "__main__":
    main()
