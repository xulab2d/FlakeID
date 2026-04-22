import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from flake_ml.config import DetectorConfig
from flake_ml.detection.classical import ClassicalFlakeDetector


class DetectorTests(unittest.TestCase):
    def test_detector_finds_synthetic_flake(self) -> None:
        image = np.full((256, 256, 3), 0.72, dtype=np.float32)
        image[90:160, 100:170, :] = np.array([0.46, 0.53, 0.60], dtype=np.float32)
        detector = ClassicalFlakeDetector(DetectorConfig(min_area_px=200, border_crop_px=2))
        result = detector.detect(image)
        self.assertGreaterEqual(len(result.candidates), 1)
        self.assertGreater(result.candidates[0].area_px, 1000)


if __name__ == "__main__":
    unittest.main()

