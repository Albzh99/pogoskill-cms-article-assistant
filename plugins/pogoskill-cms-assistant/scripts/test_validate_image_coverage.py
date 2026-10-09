import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("validate-image-coverage.py")
SPEC = importlib.util.spec_from_file_location("validate_image_coverage", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def structure(*entries, text_prefix="block"):
    return {"blocks": [
        {"type": "paragraph", "text": f"{text_prefix} {index}", "images": [entry]}
        for index, entry in enumerate(entries)
    ]}


def item(key, entry):
    base = f"https://tw.pogoskill.com/images/pikmin/{key}"
    return {
        "image_key": key,
        "source_entry": f"word/{entry}",
        "status": "image_published",
        "fallback_public_url": base + ".png",
        "webp_public_url": base + ".webp",
    }


def html_for(*items):
    return "".join(
        f'<source data-srcset="{entry["webp_public_url"]}"><img data-src="{entry["fallback_public_url"]}">'
        for entry in items
    )


class ImageCoverageTests(unittest.TestCase):
    def test_rejects_manifest_missing_one_source_image(self):
        first = item("img-01", "media/image1.png")
        result = MODULE.validate(
            structure("media/image1.png", "media/image2.png"),
            {"items": [first]},
            html_for(first),
        )
        self.assertFalse(result["pass"])
        self.assertEqual(result["source_embedded_image_count"], 2)
        self.assertEqual(result["manifest_image_count"], 1)
        self.assertIn("word/media/image2.png", result["missing_source_entries"])

    def test_rejects_html_missing_one_manifest_image(self):
        first = item("img-01", "media/image1.png")
        second = item("img-02", "media/image2.jpg")
        result = MODULE.validate(
            structure("media/image1.png", "media/image2.jpg"),
            {"items": [first, second]},
            html_for(first),
        )
        self.assertFalse(result["pass"])
        self.assertEqual(result["missing_html_image_keys"], ["img-02"])

    def test_accepts_complete_three_way_coverage(self):
        first = item("img-01", "media/image1.png")
        second = item("img-02", "media/image2.jpg")
        result = MODULE.validate(
            structure("media/image1.png", "media/image2.jpg"),
            {"items": [first, second]},
            html_for(first, second),
        )
        self.assertTrue(result["pass"], result["errors"])
        self.assertEqual(result["html_manifest_image_count"], 2)

    def test_duplicate_source_reference_requires_two_manifest_occurrences(self):
        first = item("img-01", "media/shared.png")
        result = MODULE.validate(
            structure("media/shared.png", "media/shared.png"),
            {"items": [first]},
            html_for(first),
        )
        self.assertFalse(result["pass"])
        self.assertEqual(result["missing_source_entries"], ["word/media/shared.png"])

    def test_rejects_unpublished_or_pending_image(self):
        first = item("img-01", "media/image1.png")
        first["status"] = "uploaded"
        result = MODULE.validate(
            structure("media/image1.png"),
            {"items": [first]},
            html_for(first) + "<!-- IMAGE_PENDING -->",
        )
        self.assertFalse(result["pass"])
        self.assertEqual(result["unpublished_image_keys"], ["img-01"])
        self.assertEqual(result["pending_placeholder_count"], 1)

    def test_rejects_named_guide_image_missing_from_html(self):
        source = {"blocks": [{
            "type": "paragraph",
            "text": "Guide 圖：guide-change-location-step-1.jpg",
            "images": [],
        }]}
        result = MODULE.validate(source, {"items": []}, "<p>step copy only</p>")
        self.assertFalse(result["pass"])
        self.assertIn("guide-change-location-step-1.jpg", result["missing_named_images"])

    def test_named_guide_fallback_and_webp_are_both_required(self):
        source = {"blocks": [{
            "type": "paragraph",
            "text": "guide-change-location-step-1.jpg",
            "images": [],
        }]}
        fallback = "https://tw.pogoskill.com/images/guides/guide-change-location-step-1.jpg"
        result = MODULE.validate(source, {"items": []}, f'<img data-src="{fallback}">')
        self.assertFalse(result["pass"])
        self.assertEqual(result["missing_named_images"], ["guide-change-location-step-1.webp"])
        complete = MODULE.validate(
            source,
            {"items": []},
            f'<source data-srcset="{fallback[:-4]}.webp"><img data-src="{fallback}">',
        )
        self.assertTrue(complete["pass"], complete["errors"])


if __name__ == "__main__":
    unittest.main()
