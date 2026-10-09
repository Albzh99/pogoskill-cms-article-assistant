"""Read-only install/credential/API smoke check for Windows and macOS."""

import argparse
import importlib.util
import json
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent


def image_capability():
    try:
        from PIL import features
        return bool(features.check("webp"))
    except ImportError:
        return False


def validate_site_response(response):
    if not isinstance(response, dict) or response.get("code") != 0 or not response.get("request_id"):
        raise RuntimeError("CMS site/list did not return code 0 and request_id")
    rows = response.get("data", {}).get("list")
    if not isinstance(rows, list):
        raise RuntimeError("CMS site/list did not return data.list")
    return len(rows)


def mac_site_list():
    spec = importlib.util.spec_from_file_location("cms_macos", HERE / "cms-macos.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    key = module.read_key()
    if not key:
        raise RuntimeError("CMS API key is not saved in this user's macOS Keychain")
    return module.request_json("/cms/site/list", {})


def windows_site_list(powershell=None):
    shell = powershell or shutil.which("pwsh") or shutil.which("powershell.exe")
    if not shell:
        raise RuntimeError("PowerShell was not found; pass the bundled PowerShell path with --powershell")
    with tempfile.TemporaryDirectory() as temp:
        body = Path(temp) / "body.json"
        body.write_text("{}", encoding="utf-8")
        command = [str(shell), "-NoProfile", "-File", str(HERE / "cms-request.ps1"),
                   "-Path", "/cms/site/list", "-BodyPath", str(body)]
        # PowerShell emits UTF-8 JSON; Windows Python may otherwise decode it as GBK.
        done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=120)
        if done.returncode != 0:
            raise RuntimeError("Windows CMS site/list check failed; inspect current script output without exposing Key")
        if not done.stdout:
            raise RuntimeError("Windows CMS site/list check returned no JSON output")
        return json.loads(done.stdout)


def check(system=None, powershell=None):
    system = system or platform.system()
    if system == "Windows":
        response = windows_site_list(powershell)
    elif system == "Darwin":
        response = mac_site_list()
    else:
        raise RuntimeError("This plugin currently supports Windows and macOS only")
    return {"pass": True, "platform": system, "cms_site_count": validate_site_response(response),
            "request_id": response["request_id"], "webp_encoder_available": image_capability(),
            "key_displayed": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--powershell", help="Windows only: absolute path to pwsh or powershell.exe")
    args = parser.parse_args()
    try:
        result = check(powershell=args.powershell)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        result = {"pass": False, "platform": platform.system(), "error": str(exc), "key_displayed": False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["pass"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
