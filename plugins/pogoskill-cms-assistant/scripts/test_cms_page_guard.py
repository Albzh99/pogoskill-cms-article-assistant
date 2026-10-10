import importlib.util
import unittest
from pathlib import Path


SPEC = importlib.util.spec_from_file_location("cms_page_guard", Path(__file__).with_name("cms-page-guard.py"))
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


class PageGuardTests(unittest.TestCase):
    def setUp(self):
        self.categories = {"code": 0, "request_id": "classification-read",
                           "data": {"list": [
                               {"id": 465737, "classify_id": 18939, "dir": "pikmin-bloom/", "status": 1},
                               {"id": 259613, "classify_id": 12466, "dir": "game-app/", "status": 1},
                           ]}}
        self.payload = {"site_id": 324, "product_id": ["6333", "6332"],
                        "subject": "皮克敏攻略", "url": "pikmin-bloom/article.html",
                        "classify_page_id": 465737, "classify_id": 18939,
                        "content": "<div>\n  <p>Content.</p>\n</div>"}

    def test_pikmin_category_passes(self):
        self.assertEqual([], GUARD.payload_errors(self.payload))
        self.assertEqual([], GUARD.classification_errors(self.payload, self.categories))

    def test_game_app_category_is_rejected_even_if_url_matches_it(self):
        self.payload.update(classify_page_id=259613, classify_id=12466, url="game-app/pikmin-guide.html")
        self.assertTrue(any("pikmin-bloom" in error for error in
                            GUARD.classification_errors(self.payload, self.categories)))

    def test_wrong_language_products_are_rejected(self):
        self.payload["product_id"] = ["4987", "4988"]
        self.assertTrue(any("product_id" in error for error in GUARD.payload_errors(self.payload)))

    def test_compressed_large_html_is_rejected(self):
        self.payload["content"] = "<div>" + "<p>Content.</p>" * 300 + "</div>"
        self.assertTrue(any("compressed chunk" in error for error in GUARD.payload_errors(self.payload)))

    def test_category_id_and_url_must_agree(self):
        self.payload["url"] = "game-app/article.html"
        self.assertTrue(any("selected classification directory" in error for error in
                            GUARD.classification_errors(self.payload, self.categories)))


if __name__ == "__main__":
    unittest.main()
