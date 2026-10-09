import importlib.util
import tempfile
import unittest
from pathlib import Path


SPEC = importlib.util.spec_from_file_location("prepare_image_pair", Path(__file__).with_name("prepare-image-pair.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ImagePairTests(unittest.TestCase):
    def test_keeps_original_and_creates_webp(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "supplied.png"
            Image.new("RGB", (24, 12), "red").save(source)
            result = MODULE.prepare_pair(source, root / "out", "product-step-map")
            self.assertEqual(source.read_bytes(), Path(result["original"]).read_bytes())
            with Image.open(result["webp"]) as converted:
                self.assertEqual((24, 12), converted.size)
            with self.assertRaises(FileExistsError):
                MODULE.prepare_pair(source, root / "out", "product-step-map")

    def test_rejects_random_or_unsafe_name(self):
        with self.assertRaises(ValueError):
            MODULE.prepare_pair("none.jpg", "out", "Bad Name")


if __name__ == "__main__":
    unittest.main()
