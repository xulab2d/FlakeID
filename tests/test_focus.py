import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from flake_ml.processing.focus import focus_metrics, focus_metrics_for_path


class FocusMetricTests(unittest.TestCase):
    def test_sharper_image_scores_higher(self) -> None:
        image = np.zeros((128, 128, 3), dtype=np.float32)
        image[24:104, 24:104, :] = 1.0
        sharp = focus_metrics(image, crop_fraction=1.0)

        workspace = Path.cwd() / "outputs" / "test_temp" / "focus"
        workspace.mkdir(parents=True, exist_ok=True)
        path = workspace / "sharp.png"
        blurred_path = workspace / "blurred.png"
        Image.fromarray((image * 255).astype(np.uint8)).save(path)
        Image.open(path).filter(ImageFilter.GaussianBlur(radius=3)).save(blurred_path)
        blurred = focus_metrics_for_path(blurred_path, crop_fraction=1.0)

        self.assertGreater(sharp["tenengrad"], blurred["tenengrad"])
        self.assertGreater(sharp["variance_of_laplacian"], blurred["variance_of_laplacian"])


if __name__ == "__main__":
    unittest.main()
