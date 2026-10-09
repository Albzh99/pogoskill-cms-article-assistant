"""Preserve an original JPG/PNG and create same-stem WebP on either OS."""

import argparse
import json
import re
import shutil
from pathlib import Path


SAFE_STEM = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def prepare_pair(source, output_dir, stem, quality=85):
    try:
        from PIL import Image, ImageOps, features
    except ImportError as exc:
        raise RuntimeError("Pillow is required; ask the AI to locate the bundled Python/Pillow runtime") from exc
    if not features.check("webp"):
        raise RuntimeError("This Python/Pillow runtime cannot encode WebP")
    source = Path(source)
    output_dir = Path(output_dir)
    if not source.is_file() or source.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        raise ValueError("Input must be an existing JPG/JPEG/PNG")
    if not SAFE_STEM.fullmatch(stem):
        raise ValueError("Semantic image stem must be lowercase words separated by hyphens")
    if not 1 <= quality <= 100:
        raise ValueError("WebP quality must be 1-100")
    output_dir.mkdir(parents=True, exist_ok=True)
    original = output_dir / (stem + source.suffix.lower())
    webp = output_dir / (stem + ".webp")
    if original.exists() or webp.exists():
        raise FileExistsError("Target image already exists; inspect CMS and local output before retrying")
    with Image.open(source) as image:
        converted = ImageOps.exif_transpose(image)
        width, height = converted.size
        if converted.mode not in {"RGB", "RGBA"}:
            converted = converted.convert("RGBA" if "A" in converted.getbands() else "RGB")
        converted.save(webp, "WEBP", quality=quality, method=6)
    shutil.copy2(source, original)
    return {"source": str(source), "original": str(original), "webp": str(webp),
            "width": width, "height": height}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--stem", required=True)
    parser.add_argument("--quality", type=int, default=85)
    args = parser.parse_args()
    print(json.dumps(prepare_pair(args.input, args.output_dir, args.stem, args.quality),
        ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
