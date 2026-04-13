from __future__ import annotations

import cv2
import numpy as np


def focus_score(image: np.ndarray) -> float:
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    return float(cv2.Laplacian(gray, cv2.CV_32F).var())
