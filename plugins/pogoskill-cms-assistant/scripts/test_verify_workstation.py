import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("verify_workstation", Path(__file__).with_name("verify-workstation.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PreflightTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
