"""macOS CMS credential and POST transport using Keychain and Python stdlib.

No API key is accepted on the command line, written to a file, or printed.
This file is intentionally separate from the existing Windows DPAPI scripts.
"""

import argparse
import ctypes
import getpass
import importlib.util
import io
import json
import mimetypes
import re
import secrets
import subprocess
import sys
from pathlib import Path
from urllib import error, request


SERVICE = b"TenorshareCMS/OpenAPI"
BASE_URL = "https://gw.afirstsoft.com"
KEY_PATTERN = re.compile(r"^AFS[0-9A-Za-z-]{17,}$")
CMS_PATH = re.compile(r"^/cms/[a-z0-9/_-]+$")
FILE_NAME = re.compile(r"^[a-z0-9_.-]{4,255}$")
_GUARD_SPEC = importlib.util.spec_from_file_location("cms_page_guard", Path(__file__).with_name("cms-page-guard.py"))
_GUARD = importlib.util.module_from_spec(_GUARD_SPEC)
_GUARD_SPEC.loader.exec_module(_GUARD)

def require_macos():
    if sys.platform != "darwin":
        raise RuntimeError("cms-macos.py requires macOS; Windows uses the existing PowerShell scripts")


def security_framework():
    require_macos()
    api = ctypes.CDLL("/System/Library/Frameworks/Security.framework/Security")
    ptr = ctypes.c_void_p
    length = ctypes.c_uint32
    api.SecKeychainFindGenericPassword.argtypes = [ptr, length, ctypes.c_char_p, length,
        ctypes.c_char_p, ctypes.POINTER(length), ctypes.POINTER(ptr), ctypes.POINTER(ptr)]
    api.SecKeychainFindGenericPassword.restype = ctypes.c_int32
    api.SecKeychainAddGenericPassword.argtypes = [ptr, length, ctypes.c_char_p, length,
        ctypes.c_char_p, length, ptr, ctypes.POINTER(ptr)]
    api.SecKeychainAddGenericPassword.restype = ctypes.c_int32
    api.SecKeychainItemModifyAttributesAndData.argtypes = [ptr, ptr, length, ptr]
    api.SecKeychainItemModifyAttributesAndData.restype = ctypes.c_int32
    api.SecKeychainItemFreeContent.argtypes = [ptr, ptr]
    api.SecKeychainItemFreeContent.restype = ctypes.c_int32
    core = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
    core.CFRelease.argtypes = [ptr]
    return api, core


def account_bytes():
    return getpass.getuser().encode("utf-8")


def read_key(api=None):
    api = api or security_framework()[0]
    account = account_bytes()
    size = ctypes.c_uint32(0)
    data = ctypes.c_void_p()
    status = api.SecKeychainFindGenericPassword(None, len(SERVICE), SERVICE, len(account), account,
        ctypes.byref(size), ctypes.byref(data), None)
    if status == -25300:  # errSecItemNotFound
        return None
    if status != 0:
        raise RuntimeError(f"macOS Keychain read failed, status={status}")
    try:
        key = ctypes.string_at(data, size.value).decode("utf-8").strip()
    finally:
        api.SecKeychainItemFreeContent(None, data)
    if not KEY_PATTERN.fullmatch(key):
        raise RuntimeError("Stored CMS API key is invalid")
    return key


def save_key(key, api=None, core=None):
    if not KEY_PATTERN.fullmatch(key):
        raise ValueError("Clipboard does not contain a complete CMS API key")
    if api is None or core is None:
        api, core = security_framework()
    account = account_bytes()
    raw = key.encode("utf-8")
    buffer = ctypes.create_string_buffer(raw)
    item = ctypes.c_void_p()
    status = api.SecKeychainAddGenericPassword(None, len(SERVICE), SERVICE, len(account), account,
        len(raw), ctypes.cast(buffer, ctypes.c_void_p), ctypes.byref(item))
    if status == -25299:  # errSecDuplicateItem: update only this service/account
        found = api.SecKeychainFindGenericPassword(None, len(SERVICE), SERVICE, len(account), account,
            None, None, ctypes.byref(item))
        if found != 0:
            raise RuntimeError(f"macOS Keychain item lookup failed, status={found}")
        try:
            status = api.SecKeychainItemModifyAttributesAndData(item, None, len(raw),
                ctypes.cast(buffer, ctypes.c_void_p))
        finally:
            core.CFRelease(item)
    elif item.value:
        core.CFRelease(item)
    ctypes.memset(buffer, 0, len(buffer))
    if status != 0:
        raise RuntimeError(f"macOS Keychain save failed, status={status}")


def checked_response(raw, endpoint):
    try:
        result = json.loads(raw)
    except (UnicodeDecodeError, ValueError) as exc:
        raise RuntimeError(f"CMS returned non-JSON data on {endpoint}") from exc
    if not isinstance(result, dict) or result.get("code") != 0:
        code = result.get("code") if isinstance(result, dict) else None
        message = result.get("msg") if isinstance(result, dict) else None
        reqid = result.get("request_id") if isinstance(result, dict) else None
        raise RuntimeError(f"CMS business error on {endpoint}: code={code}, request_id={reqid}, msg={message}")
    if not result.get("request_id"):
        raise RuntimeError(f"CMS response on {endpoint} has no request_id")
    return result


def cms_post(endpoint, body, content_type="application/json; charset=utf-8", api_key=None):
    if not CMS_PATH.fullmatch(endpoint):
        raise ValueError("CMS endpoint must be a /cms/ path")
    key = api_key or read_key()
    if not key:
        raise RuntimeError("CMS API key not found in this user's macOS Keychain")
    req = request.Request(BASE_URL + endpoint, data=body, method="POST",
        headers={"X-API-KEY": key, "Accept": "application/json", "Content-Type": content_type})
    try:
        with request.urlopen(req, timeout=90) as response:
            raw = response.read()
    except error.HTTPError as exc:
        raise RuntimeError(f"CMS HTTP error on {endpoint}: status={exc.code}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"CMS transport error on {endpoint}: {exc.reason}") from exc
    return checked_response(raw, endpoint)


def request_json(endpoint, payload, api_key=None, allow_image_publish=False):
    if not isinstance(payload, dict):
        raise ValueError("CMS request body must be a JSON object")
    if endpoint == "/cms/page/make" or "delete" in endpoint or "remove" in endpoint:
        raise ValueError("Page generation and deletion are forbidden in this assistant")
    if endpoint == "/cms/pagepublish/publish" and not allow_image_publish:
        raise ValueError("Use publish-image with a saved picture/upload response")
    if endpoint in {"/cms/page/add", "/cms/page/update"}:
        errors = _GUARD.payload_errors(payload)
        if errors:
            raise ValueError("; ".join(errors))
        classification = cms_post(
            "/cms/classify/displayclassifylist",
            json.dumps({"site_id": payload["site_id"]}).encode("utf-8"),
            api_key=api_key,
        )
        errors = _GUARD.classification_errors(payload, classification)
        if errors:
            raise ValueError("; ".join(errors))
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return cms_post(endpoint, body, api_key=api_key)


def multipart_image_body(site_id, cms_path, files):
    if not isinstance(site_id, int) or site_id <= 0 or not files or len(files) > 100:
        raise ValueError("site_id and 1-100 image files are required")
    boundary = "----TenorshareCMS" + secrets.token_hex(16)
    out = io.BytesIO()
    for name, value in (("site_id", str(site_id)), ("path", cms_path)):
        out.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode())
    for path in files:
        file = Path(path)
        if not file.is_file() or not FILE_NAME.fullmatch(file.name):
            raise ValueError(f"Image missing or filename invalid: {file.name}")
        if file.stat().st_size > 30 * 1024 * 1024:
            raise ValueError(f"Image exceeds 30 MB: {file.name}")
        out.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"files[]\"; filename=\"{file.name}\"\r\n".encode())
        out.write(f"Content-Type: {mimetypes.guess_type(file.name)[0] or 'application/octet-stream'}\r\n\r\n".encode())
        out.write(file.read_bytes())
        out.write(b"\r\n")
    out.write(f"--{boundary}--\r\n".encode())
    return out.getvalue(), f"multipart/form-data; boundary={boundary}"


def write_result(result, output):
    serialized = json.dumps(result, ensure_ascii=False, indent=2)
    if output:
        Path(output).write_text(serialized + "\n", encoding="utf-8")
    print(serialized)


def main():
    require_macos()
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check-key")
    commands.add_parser("save-key")
    req = commands.add_parser("request")
    req.add_argument("--path", required=True)
    req.add_argument("--body", required=True)
    req.add_argument("--output")
    req.add_argument("--execute", action="store_true")
    upload = commands.add_parser("upload-image")
    upload.add_argument("--site-id", type=int, required=True)
    upload.add_argument("--cms-path", default="")
    upload.add_argument("--file", action="append", required=True)
    upload.add_argument("--output", required=True)
    upload.add_argument("--execute", action="store_true", required=True)
    publish = commands.add_parser("publish-image")
    publish.add_argument("--upload-response", required=True)
    publish.add_argument("--output", required=True)
    publish.add_argument("--execute", action="store_true", required=True)
    args = parser.parse_args()
    if args.command == "check-key":
        if not read_key():
            raise RuntimeError("No CMS API key in this user's macOS Keychain")
        print("CMS API key is available; value not displayed.")
    elif args.command == "save-key":
        print("请现在复制管理员给你的完整 CMS API Key。复制后回到这个窗口，只按 Enter。", flush=True)
        input()
        key = subprocess.run(["pbpaste"], check=True, capture_output=True, text=True).stdout.strip()
        save_key(key)
        subprocess.run(["pbcopy"], input=" ", check=True, text=True)
        if not read_key():
            raise RuntimeError("Keychain verification failed after saving")
        print("CMS API key saved in macOS Keychain and verified; clipboard cleared.")
    elif args.command == "request":
        if args.path in {"/cms/page/add", "/cms/page/update"} and not args.execute:
            raise ValueError("Page writes require --execute after preflight validation")
        payload = json.loads(Path(args.body).read_text(encoding="utf-8-sig"))
        write_result(request_json(args.path, payload), args.output)
    elif args.command == "upload-image":
        body, content_type = multipart_image_body(args.site_id, args.cms_path, args.file)
        result = cms_post("/cms/picture/upload", body, content_type)
        data = result.get("data", {})
        if not isinstance(data, dict) or not isinstance(data.get("publish_id"), int) or not data.get("list"):
            raise RuntimeError("Image upload did not return publish_id and file list")
        write_result(result, args.output)
    elif args.command == "publish-image":
        upload = json.loads(Path(args.upload_response).read_text(encoding="utf-8-sig"))
        if upload.get("code") != 0 or not upload.get("request_id"):
            raise ValueError("Saved image upload response lacks successful request evidence")
        data = upload.get("data", {})
        publish_id = data.get("publish_id") if isinstance(data, dict) else None
        if type(publish_id) is not int or publish_id <= 0 or not data.get("list"):
            raise ValueError("Saved image upload response lacks a valid image publish_id")
        result = request_json("/cms/pagepublish/publish", {"id": publish_id, "description": "同步图片资源"},
            allow_image_publish=True)
        details = result.get("data", {})
        success = details.get("success", []) if isinstance(details, dict) else []
        failed = details.get("failed", []) if isinstance(details, dict) else []
        if failed or not any(str(item.get("id")) == str(publish_id) for item in success if isinstance(item, dict)):
            raise RuntimeError(f"Image resource publish did not confirm id={publish_id}")
        write_result(result, args.output)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
