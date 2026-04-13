import unittest

import numpy as np

from flakefinder.config.loader import load_app_config
from flakefinder.detection.detector_2dmatgmm import Detector2DMatGMM


class DetectorInterfaceTests(unittest.TestCase):
    def test_detector_returns_candidates(self) -> None:
        config = load_app_config("configs/mock_gr285_graphene.yaml")
        detector = Detector2DMatGMM(config)
        image = np.zeros((128, 128, 3), dtype=np.uint8)
        image[30:70, 30:80] = 255
        candidates = detector.detect(image)
        self.assertIsInstance(candidates, list)


if __name__ == "__main__":
    unittest.main()
