from __future__ import annotations

import cv2
import numpy as np

from flakefinder.config.models import AppConfig

from .darkframe import subtract_darkframe
from .demosaic import demosaic_if_needed
from .flatfield import apply_flatfield


def _to_uint8(image: np.ndarray, low_pct: float, high_pct: float) -> np.ndarray:
    image_f = image.astype(np.float32)
    low, high = np.percentile(image_f, [low_pct, high_pct])
    if high <= low:
        high = low + 1.0
    scaled = np.clip((image_f - low) / (high - low), 0.0, 1.0)
    if scaled.ndim == 2:
        scaled = np.stack([scaled, scaled, scaled], axis=-1)
    return (scaled * 255).astype(np.uint8)


def preprocess_image(image: np.ndarray, config: AppConfig) -> tuple[np.ndarray, np.ndarray]:
    processed = demosaic_if_needed(image, config.preprocessing.demosaic)
    if config.preprocessing.darkframe_subtraction:
        processed = subtract_darkframe(processed, config.preprocessing.darkframe_path)
    if config.preprocessing.flatfield_correction:
        processed = apply_flatfield(processed, config.preprocessing.flatfield_path)
    preview = _to_uint8(
        processed,
        config.preprocessing.clip_percentile_low,
        config.preprocessing.clip_percentile_high,
    )
    if config.preprocessing.normalize_background:
        preview = cv2.cvtColor(preview, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(preview)
        l_channel = cv2.equalizeHist(l_channel)
        preview = cv2.merge([l_channel, a_channel, b_channel])
        preview = cv2.cvtColor(preview, cv2.COLOR_LAB2BGR)
    return processed, preview
