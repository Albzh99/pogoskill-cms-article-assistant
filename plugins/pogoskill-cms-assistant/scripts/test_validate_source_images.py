import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("validate-source-images.py")
SPEC = importlib.util.spec_from_file_location("validate_source_images", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SourceImageTests(unittest.TestCase):
    def test_single_format_site_can_pass(self):
        structure = {"blocks": [{"images": ["media/one.png"]}]}
        url = "https://images.example.com/article/one.png"
        manifest = {"items": [{"image_key": "one", "source_entry": "word/media/one.png", "html_urls": [url], "status": "image_published"}]}
        result = MODULE.check(structure, manifest, f'<img src="{url}">')
        self.assertTrue(result["pass"], result["errors"])

    def test_duplicate_media_reference_requires_each_occurrence(self):
        structure = {"blocks": [{"images": ["media/one.png", "media/one.png"]}]}
        url = "https://images.example.com/article/one.png"
        manifest = {"items": [{"image_key": "one", "source_entry": "word/media/one.png", "html_urls": [url], "status": "image_published"}]}
        result = MODULE.check(structure, manifest, f'<img src="{url}">')
        self.assertFalse(result["pass"])
        self.assertEqual(result["missing_source_entries"], ["word/media/one.png"])

    def test_same_image_twice_needs_two_html_positions(self):
        structure = {"blocks": [{"images": ["media/one.png", "media/one.png"]}]}
        url = "https://images.example.com/article/one.png"
        manifest = {"items": [
            {"image_key": "one-a", "source_entry": "media/one.png", "html_urls": [url], "status": "image_published"},
            {"image_key": "one-b", "source_entry": "media/one.png", "html_urls": [url], "status": "image_published"},
        ]}
        result = MODULE.check(structure, manifest, f'<img src="{url}">')
        self.assertFalse(result["pass"])
        self.assertTrue(result["missing_html_image_keys"])

    def test_required_formats_are_manifest_driven(self):
        structure = {"blocks": [{"images": ["media/one.jpg"]}]}
        base = "https://images.example.com/article/one"
        manifest = {"items": [{"image_key": "one", "source_entry": "media/one.jpg", "status": "image_published",
                               "html_urls": [base + ".jpg", base + ".webp"]}]}
        result = MODULE.check(structure, manifest, f'<img src="{base}.jpg">')
        self.assertFalse(result["pass"])
        self.assertEqual(result["missing_html_image_keys"], ["one"])

    def test_accepts_shared_pair_uploader_manifest_fields(self):
        structure = {"blocks": [{"images": ["media/one.jpg"]}]}
        base = "https://images.example.com/article/one"
        manifest = {"items": [{"image_key": "one", "source_entry": "media/one.jpg", "status": "image_published",
                               "fallback_public_url": base + ".jpg",
                               "webp_public_url": base + ".webp"}]}
        markup = f'<picture><source data-srcset="{base}.webp"><img data-src="{base}.jpg"></picture>'
        self.assertTrue(MODULE.check(structure, manifest, markup)["pass"])

    def test_uploaded_but_unpublished_image_is_blocked(self):
        structure = {"blocks": [{"images": ["media/one.png"]}]}
        url = "https://images.example.com/article/one.png"
        manifest = {"items": [{"image_key": "one", "source_entry": "media/one.png",
                               "html_urls": [url], "status": "uploaded_pending_publish"}]}
        result = MODULE.check(structure, manifest, f'<img src="{url}">')
        self.assertFalse(result["pass"])
        self.assertEqual(result["unpublished_image_keys"], ["one"])


if __name__ == "__main__":
    unittest.main()
