import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("cms_macos", Path(__file__).with_name("cms-macos.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MacTransportTests(unittest.TestCase):
    def test_save_key_rejects_integrated_terminal(self):
        with patch.dict(MODULE.os.environ, {"TERM_PROGRAM": "Codex",
                                            "POGOSKILL_CMS_TERMINAL_LAUNCH": "1"}):
            with self.assertRaisesRegex(RuntimeError, "Terminal.app"):
                MODULE.require_external_terminal()

    def test_external_terminal_signal_required(self):
        with tempfile.TemporaryDirectory() as temp:
            observed = {}
            def launch(command, **_kwargs):
                launcher = Path(command[3])
                observed["content"] = launcher.read_text(encoding="utf-8")
                launcher.with_suffix(".ready").write_text("Apple_Terminal", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0)
            with patch.object(MODULE, "require_macos"), patch.object(
                    MODULE.subprocess, "run", side_effect=launch), patch("builtins.print") as announcement:
                MODULE.open_save_key_terminal(temp)
            announcement.call_args.args[0].encode("cp1252")
            self.assertIn("TERM_PROGRAM", observed["content"])
            self.assertNotIn("X-API-KEY", observed["content"])
            self.assertEqual(list(Path(temp).iterdir()), [])
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(MODULE, "require_macos"), patch.object(
                    MODULE.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)), patch.object(
                    MODULE, "wait_for_external_terminal", return_value=False):
                with self.assertRaisesRegex(RuntimeError, "did not start the key prompt"):
                    MODULE.open_save_key_terminal(temp)

    def test_403_reports_request_id_but_never_key(self):
        summary = MODULE.http_error_summary(403, "/cms/site/list",
            b'{"code":403,"msg":"key secret-key denied"}', "secret-key",
            b"X-Request-ID: gateway-42\r\n")
        self.assertIn("status=403", summary)
        self.assertIn("gateway-42", summary)
        self.assertNotIn("secret-key", summary)

    def test_curl_transport_keeps_key_out_of_argv_and_files(self):
        key = "AFS1727-0001-example-valid-key"
        seen = {}
        def run(command, **kwargs):
            seen["argv"] = command
            seen["stdin"] = kwargs["input"]
            Path(command[command.index("--output") + 1]).write_bytes(b'{"code":0,"request_id":"ok"}')
            Path(command[command.index("--dump-header") + 1]).write_bytes(b"HTTP/2 200\r\n")
            seen["body"] = Path(command[command.index("--data-binary") + 1][1:]).read_bytes()
            return subprocess.CompletedProcess(command, 0, stdout="200", stderr="")
        with patch.object(MODULE.shutil, "which", return_value="/usr/bin/curl"), patch.object(
                MODULE.subprocess, "run", side_effect=run):
            result = MODULE.cms_post("/cms/site/list", b"{}", api_key=key)
        self.assertEqual(result["request_id"], "ok")
        self.assertEqual(seen["body"], b"{}")
        self.assertNotIn(key, " ".join(seen["argv"]))
        self.assertIn(key, seen["stdin"])

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
