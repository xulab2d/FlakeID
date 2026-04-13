from __future__ import annotations

from pathlib import Path

import numpy as np

from .raw_io import load_image


def apply_flatfield(image: np.ndarray, flatfield_path: str | None) -> np.ndarray:
    if not flatfield_path:
        return image
    flat = load_image(Path(flatfield_path)).astype(np.float32)
    image_f = image.astype(np.float32)
    corrected = image_f / np.maximum(flat, 1.0) * np.mean(flat)
    return np.clip(corrected, 0, np.iinfo(image.dtype).max if np.issubdtype(image.dtype, np.integer) else 1.0).astype(image.dtype)
