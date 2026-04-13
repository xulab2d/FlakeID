import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from flakefinder.pipelines.scan_and_detect import run_mock_scan


class MockPipelineTests(unittest.TestCase):
    def test_mock_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir)
            input_dir = base / "tiles"
            input_dir.mkdir()
            image = np.zeros((128, 128, 3), dtype=np.uint8)
            cv2.rectangle(image, (30, 30), (90, 90), (255, 255, 255), -1)
            cv2.imwrite(str(input_dir / "tile_0.png"), image)
            output_dir = base / "run"
            result = run_mock_scan("configs/mock_bn90_hbn.yaml", str(input_dir), str(output_dir))
            self.assertEqual(result["tiles"], 1)
            self.assertTrue((output_dir / "storage" / "flakefinder.db").exists())


if __name__ == "__main__":
    unittest.main()
