import unittest
from pathlib import Path

from flakefinder.config.loader import load_app_config


class ConfigTests(unittest.TestCase):
    def test_load_config(self) -> None:
        config = load_app_config(Path("configs/mock_bn90_hbn.yaml"))
        self.assertEqual(config.config_key, "bn90_hbn")
        self.assertEqual(config.hardware.backend, "mock")


if __name__ == "__main__":
    unittest.main()
