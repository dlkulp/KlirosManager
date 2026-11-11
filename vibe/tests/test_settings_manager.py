import json
import tempfile
import unittest
from pathlib import Path

from settings_manager import SettingsManager


class SettingsManagerTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.settings_path = self.root / "settings.json"

    def test_defaults_and_extensible_settings_persist(self):
        settings = SettingsManager(self.settings_path, project_root=self.root)

        self.assertEqual(settings.get("storage_folder"), "uploads")
        self.assertEqual(settings.get("max_hamming_distance"), 10)
        self.assertEqual(settings.get("invalid_hamming_distance"), 50)
        self.assertFalse(settings.get("extract_pdf_text"))
        self.assertEqual(settings.reference_image_path(), (self.root / "references").resolve())
        settings.set("max_hamming_distance", 3)
        settings.set("invalid_hamming_distance", 25)
        settings.set("reference_image_path", "reference.png")
        settings.set("extract_pdf_text", True)
        settings.set("future_option", {"enabled": True})
        reopened = SettingsManager(self.settings_path, project_root=self.root)

        self.assertEqual(reopened.get("max_hamming_distance"), 3)
        self.assertEqual(reopened.get("invalid_hamming_distance"), 25)
        self.assertEqual(reopened.reference_image_path(), (self.root / "reference.png").resolve())
        self.assertTrue(reopened.get("extract_pdf_text"))
        self.assertEqual(reopened.get("future_option"), {"enabled": True})
        self.assertTrue(reopened.storage_path().is_dir())
        self.assertEqual(json.loads(self.settings_path.read_text(encoding="utf-8"))["future_option"], {"enabled": True})

    def test_rejects_negative_hamming_threshold(self):
        self.settings_path.write_text(json.dumps({"max_hamming_distance": -1}), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "non-negative"):
            SettingsManager(self.settings_path, project_root=self.root)

    def test_invalid_hamming_distance_must_fit_the_64_bit_hash(self):
        for value in (-1, 65, True):
            with self.subTest(value=value):
                self.settings_path.write_text(json.dumps({"invalid_hamming_distance": value}), encoding="utf-8")

                with self.assertRaisesRegex(ValueError, "between 0 and 64"):
                    SettingsManager(self.settings_path, project_root=self.root)

    def test_reference_image_path_must_be_non_empty(self):
        self.settings_path.write_text(json.dumps({"reference_image_path": "  "}), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "reference_image_path"):
            SettingsManager(self.settings_path, project_root=self.root)

    def test_extract_pdf_text_must_be_a_boolean(self):
        self.settings_path.write_text(json.dumps({"extract_pdf_text": "false"}), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "extract_pdf_text"):
            SettingsManager(self.settings_path, project_root=self.root)


if __name__ == "__main__":
    unittest.main()