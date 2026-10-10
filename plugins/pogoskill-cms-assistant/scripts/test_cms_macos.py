import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("cms_macos", Path(__file__).with_name("cms-macos.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MacTransportTests(unittest.TestCase):
    def test_multipart_contains_files_and_no_key(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "article-image.jpg"
            file.write_bytes(b"image-bytes")
            body, content_type = MODULE.multipart_image_body(44, "blog", [file])
        self.assertIn(b'filename="article-image.jpg"', body)
        self.assertIn(b"image-bytes", body)
        self.assertIn(b'name="site_id"', body)
        self.assertTrue(content_type.startswith("multipart/form-data; boundary="))

    def test_rejects_invalid_file_name(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "Bad Name.JPG"
            file.write_bytes(b"bytes")
            with self.assertRaises(ValueError):
                MODULE.multipart_image_body(44, "blog", [file])

    def test_response_requires_business_success_and_request_id(self):
        self.assertEqual(0, MODULE.checked_response(b'{"code":0,"request_id":"ok"}', "/cms/site/list")["code"])
        with self.assertRaises(RuntimeError):
            MODULE.checked_response(b'{"code":0}', "/cms/site/list")
        with self.assertRaises(RuntimeError):
            MODULE.checked_response(b'{"code":60001,"request_id":"bad"}', "/cms/site/list")

    def test_visible_newline_tokens_rejected_before_request(self):
        payload = {"site_id": 324, "product_id": ["6333", "6332"],
                   "content": "part 1\\npart 2"}
        with patch.object(MODULE, "cms_post") as post:
            with self.assertRaisesRegex(ValueError, "escaped-newline"):
                MODULE.request_json("/cms/page/add", payload, api_key="placeholder")
            post.assert_not_called()

    def test_page_write_checks_live_classification_before_post(self):
        payload = {"site_id": 324, "product_id": ["6333", "6332"],
                   "subject": "皮克敏攻略", "url": "game-app/pikmin-guide.html",
                   "classify_id": 12466, "classify_page_id": 259613,
                   "content": "<div>\n<p>Content.</p>\n</div>"}
        categories = {"code": 0, "request_id": "read", "data": {"list": [
            {"id": 259613, "classify_id": 12466, "dir": "game-app/", "status": 1}
        ]}}
        with patch.object(MODULE, "cms_post", return_value=categories) as post:
            with self.assertRaisesRegex(ValueError, "pikmin-bloom"):
                MODULE.request_json("/cms/page/add", payload, api_key="placeholder")
            self.assertEqual(post.call_count, 1)
            self.assertEqual(post.call_args.args[0], "/cms/classify/displayclassifylist")

    def test_english_page_write_keeps_english_products_and_classification(self):
        payload = {"site_id": 286, "product_id": ["4987", "4988"],
                   "subject": "Pikmin Bloom guide", "url": "pikmin-bloom/article.html",
                   "classify_id": 77, "classify_page_id": 88,
                   "content": "<div>\n<p>Complete content.</p>\n</div>"}
        categories = {"code": 0, "request_id": "read", "data": {"list": [
            {"id": 88, "classify_id": 77, "dir": "pikmin-bloom/", "status": 1}
        ]}}
        response = {"code": 0, "request_id": "write", "data": {"id": 1}}
        with patch.object(MODULE, "cms_post", side_effect=[categories, response]) as post:
            self.assertEqual(MODULE.request_json("/cms/page/add", payload, api_key="placeholder"), response)
            self.assertEqual([call.args[0] for call in post.call_args_list],
                             ["/cms/classify/displayclassifylist", "/cms/page/add"])

if __name__ == "__main__":
    unittest.main()
