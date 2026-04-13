from __future__ import annotations

from pathlib import Path

import numpy as np

from .raw_io import load_image


def subtract_darkframe(image: np.ndarray, darkframe_path: str | None) -> np.ndarray:
    if not darkframe_path:
        return image
    dark = load_image(Path(darkframe_path)).astype(np.float32)
    corrected = image.astype(np.float32) - dark
    return np.clip(corrected, 0, None).astype(image.dtype)
