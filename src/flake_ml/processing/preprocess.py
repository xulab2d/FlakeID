from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


def load_image(path: str | Path) -> np.ndarray:
    image = Image.open(path).convert("RGB")
    return np.asarray(image, dtype=np.float32) / 255.0


def save_image(image: np.ndarray, path: str | Path) -> None:
    clipped = np.clip(image, 0.0, 1.0)
    array = (clipped * 255.0).astype(np.uint8)
    Image.fromarray(array, mode="RGB").save(path)


def estimate_background(image: np.ndarray, shrink_to: int = 48) -> np.ndarray:
    pil_image = Image.fromarray((np.clip(image, 0.0, 1.0) * 255.0).astype(np.uint8), mode="RGB")
    width, height = pil_image.size
    scale = max(width, height) / max(shrink_to, 1)
    reduced = pil_image.resize((max(1, int(width / scale)), max(1, int(height / scale))), Image.Resampling.BICUBIC)
    expanded = reduced.resize((width, height), Image.Resampling.BICUBIC)
    return np.asarray(expanded, dtype=np.float32) / 255.0


def build_flat_field(images: list[np.ndarray]) -> np.ndarray:
    if not images:
        raise ValueError("At least one image is required to build a flat field.")
    stack = np.stack(images, axis=0)
    mean_image = np.mean(stack, axis=0)
    baseline = np.mean(mean_image, axis=(0, 1), keepdims=True)
    return np.clip(mean_image / np.maximum(baseline, 1e-6), 1e-3, None)


def apply_flat_field(image: np.ndarray, flat_field: np.ndarray) -> np.ndarray:
    corrected = image / np.maximum(flat_field, 1e-6)
    scale = np.mean(corrected, axis=(0, 1), keepdims=True)
    return np.clip(corrected / np.maximum(scale, 1e-6), 0.0, 1.0)


def white_balance_from_border(image: np.ndarray, border_fraction: float = 0.05) -> np.ndarray:
    height, width, _ = image.shape
    border = max(1, int(min(height, width) * border_fraction))
    samples = np.concatenate(
        [
            image[:border, :, :].reshape(-1, 3),
            image[-border:, :, :].reshape(-1, 3),
            image[:, :border, :].reshape(-1, 3),
            image[:, -border:, :].reshape(-1, 3),
        ],
        axis=0,
    )
    reference = np.median(samples, axis=0, keepdims=True)
    gray = float(np.mean(reference))
    gains = gray / np.maximum(reference, 1e-6)
    return np.clip(image * gains.reshape(1, 1, 3), 0.0, 1.0)

