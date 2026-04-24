import unittest
from pathlib import Path

from flake_ml.config_store import update_toml_section


class ConfigStoreTests(unittest.TestCase):
    def test_update_motion_section_replaces_and_inserts_values(self) -> None:
        original = (
            "[lab]\n"
            'name = "Microscope"\n'
            "\n"
            "[motion]\n"
            "port = \"COM3\"\n"
            "baud = 115200\n"
        )
        workspace_temp = Path.cwd() / "outputs" / "test_temp"
        workspace_temp.mkdir(parents=True, exist_ok=True)
        path = workspace_temp / "config_store_test.toml"
        try:
            path.write_text(original, encoding="utf-8")
            update_toml_section(
                path,
                "motion",
                {
                    "baud": 57600,
                    "max_x_um": 100000.0,
                },
            )
            text = path.read_text(encoding="utf-8")
            self.assertIn("baud = 57600", text)
            self.assertIn("max_x_um = 100000", text)
        finally:
            if path.exists():
                path.unlink()


if __name__ == "__main__":
    unittest.main()
