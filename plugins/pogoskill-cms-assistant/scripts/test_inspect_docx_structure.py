import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path


SPEC = importlib.util.spec_from_file_location("inspect_docx_structure",
                                              Path(__file__).with_name("inspect-docx-structure.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DocxBoldTests(unittest.TestCase):
    def test_extracts_explicit_bold_step_lead(self):
        xml = '''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:body><w:p>
            <w:r><w:t>步驟 1：</w:t></w:r>
            <w:r><w:rPr><w:b/></w:rPr><w:t>下載並安裝：</w:t></w:r>
            <w:r><w:t>開啟 PoGoskill。</w:t></w:r>
          </w:p></w:body></w:document>'''
        rels = '''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'''
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.docx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", xml)
                archive.writestr("word/_rels/document.xml.rels", rels)
            record = MODULE.inspect(path)["blocks"][0]
        self.assertEqual(record["text"], "步驟 1：下載並安裝：開啟 PoGoskill。")
        self.assertEqual(record["bold_spans"], ["下載並安裝："])


if __name__ == "__main__":
    unittest.main()
