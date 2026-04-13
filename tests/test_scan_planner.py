import unittest
from pathlib import Path

from flakefinder.acquisition.serpentine_scan import generate_serpentine_tiles
from flakefinder.config.loader import load_app_config


class ScanPlannerTests(unittest.TestCase):
    def test_serpentine_tiles(self) -> None:
        config = load_app_config(Path("configs/mock_bn90_hbn.yaml"))
        tiles = generate_serpentine_tiles(config)
        self.assertGreater(len(tiles), 0)
        self.assertEqual(tiles[0].row, 0)


if __name__ == "__main__":
    unittest.main()
