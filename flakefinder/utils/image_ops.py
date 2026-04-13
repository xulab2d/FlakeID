from __future__ import annotations

import numpy as np


def crop_thumbnail(image: np.ndarray, bbox: tuple[int, int, int, int], pad: int = 20) -> np.ndarray:
    x, y, w, h = bbox
    x0 = max(0, x - pad)
    y0 = max(0, y - pad)
    x1 = min(image.shape[1], x + w + pad)
    y1 = min(image.shape[0], y + h + pad)
    return image[y0:y1, x0:x1]
