from __future__ import annotations

import numpy as np


def demosaic_if_needed(image: np.ndarray, enabled: bool) -> np.ndarray:
    if not enabled or image.ndim == 3:
        return image
    return np.stack([image, image, image], axis=-1)
