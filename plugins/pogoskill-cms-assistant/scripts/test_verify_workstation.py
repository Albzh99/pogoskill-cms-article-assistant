import importlib.util
from types import SimpleNamespace
import unittest
from pathlib import Path
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("verify_workstation", Path(__file__).with_name("verify-workstation.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PreflightTests(unittest.TestCase):
    def test_mac_smoke_check_reads_key_once(self):
        calls = []
        fake_module = SimpleNamespace(
            read_key=lambda: calls.append("read") or "AFS-test-key",
            request_json=lambda path, body, api_key=None: calls.append((path, api_key)) or
                {"code": 0, "request_id": "r", "data": {"list": []}},
        )
        fake_spec = SimpleNamespace(loader=SimpleNamespace(exec_module=lambda _module: None))
        with patch.object(MODULE.importlib.util, "spec_from_file_location", return_value=fake_spec), patch.object(
                MODULE.importlib.util, "module_from_spec", return_value=fake_module):
            MODULE.mac_site_list()
        self.assertEqual(calls, ["read", ("/cms/site/list", "AFS-test-key")])

    def test_identity_points_to_current_plugin(self):
        identity = MODULE.plugin_identity()
        self.assertEqual("1.0.1+codex.20261014keychain2", identity["plugin_version"])
        self.assertTrue(identity["cms_script"].endswith("cms-macos.py"))

    def test_accepts_real_shape(self):
        self.assertEqual(2, MODULE.validate_site_response({"code": 0, "request_id": "r", "data": {"list": [{}, {}]}}))

    def test_requires_request_id(self):
        with self.assertRaises(RuntimeError):
            MODULE.validate_site_response({"code": 0, "data": {"list": []}})

    def test_windows_transport_decodes_utf8(self):
        response = '{"code":0,"request_id":"r","data":{"list":[{"site_name":"繁中站"}]}}'
        with patch.object(MODULE.subprocess, "run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = response
            self.assertEqual("繁中站", MODULE.windows_site_list("pwsh")["data"]["list"][0]["site_name"])
            self.assertEqual("utf-8", run.call_args.kwargs["encoding"])

    def test_missing_webp_blocks_ready_state(self):
        response = {"code": 0, "request_id": "r", "data": {"list": []}}
        with patch.object(MODULE, "windows_site_list", return_value=response), patch.object(MODULE, "image_capability", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "WebP"):
                MODULE.check(system="Windows")


if __name__ == "__main__":
    unittest.main()
