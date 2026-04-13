import unittest

import numpy as np

from flakefinder.config.loader import load_app_config
from flakefinder.imaging.normalize import preprocess_image


class PreprocessingTests(unittest.TestCase):
    def test_preprocess_returns_preview(self) -> None:
        config = load_app_config("configs/mock_bn90_hbn.yaml")
        image = np.zeros((64, 64, 3), dtype=np.uint16)
        image[20:40, 20:40] = 2000
        raw, preview = preprocess_image(image, config)
        self.assertEqual(raw.shape, image.shape)
        self.assertEqual(preview.dtype, np.uint8)


if __name__ == "__main__":
    unittest.main()
