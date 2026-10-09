import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("compare-docx-to-cms-page.py")
SPEC = importlib.util.spec_from_file_location("compare_docx_to_cms_page", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class StepCopyTests(unittest.TestCase):
    def test_extracts_chinese_and_english_step_body(self):
        self.assertEqual(MODULE.step_body("步驟 1：連接手機並開啟軟體。"), "連接手機並開啟軟體。")
        self.assertEqual(MODULE.step_body("Step 2: Search for the destination."), "Searchforthedestination.")
        self.assertIsNone(MODULE.step_body("普通正文不是步驟。"))
        self.assertTrue(MODULE.is_step_badge_only("Step 3"))

    def run_compare(self, source_text, html):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            structure = root / "structure.json"
            page = root / "page.json"
            structure.write_text(
                json.dumps({"blocks": [{"type": "paragraph", "style": "", "text": source_text, "images": []}]}),
                encoding="utf-8",
            )
            page.write_text(json.dumps({"data": {"content": html}}), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(SCRIPT), str(structure), str(page)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )

    def test_allows_markup_only_change(self):
        result = self.run_compare(
            "步驟 1：連接手機：並開啟軟體。",
            "<li><p><span>步驟 1</span><label><strong>連接手機：</strong>並開啟軟體。</label></p></li>",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["missing_step_blocks"], [])

    def test_rejects_rewritten_step_copy(self):
        result = self.run_compare(
            "Step 1: Connect your phone and open PoGoskill.",
            "<li><p><span>Step 1</span><label>Launch the app after connecting.</label></p></li>",
        )
        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["missing_step_blocks"])

    def test_checks_instruction_after_standalone_step_badge(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            structure = root / "structure.json"
            page = root / "page.json"
            structure.write_text(
                json.dumps({"blocks": [
                    {"type": "paragraph", "style": "", "text": "步驟 1", "images": []},
                    {"type": "paragraph", "style": "", "text": "下載並安裝 PoGoskill。", "images": []},
                ]}),
                encoding="utf-8",
            )
            page.write_text(
                json.dumps({"data": {"content": "<p><span>步驟 1</span><label>安裝軟體。</label></p>"}}),
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(structure), str(page)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(json.loads(result.stdout)["missing_step_blocks"])


if __name__ == "__main__":
    unittest.main()
