from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import numpy as np


def ensure_dir(path: str | Path) -> Path:
    resolved = Path(path)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def resolve_path(path: str | Path, base_dir: str | Path | None = None) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    if base_dir is None:
        return candidate.resolve()
    return (Path(base_dir) / candidate).resolve()


def timestamp_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def robust_sigma(values: np.ndarray) -> float:
    flat = np.asarray(values, dtype=np.float32).reshape(-1)
    if flat.size == 0:
        return 1.0
    median = np.median(flat)
    mad = np.median(np.abs(flat - median))
    sigma = 1.4826 * mad
    return float(max(sigma, 1e-6))


def rgb_to_hsv(image: np.ndarray) -> np.ndarray:
    image = np.clip(image.astype(np.float32), 0.0, 1.0)
    r = image[..., 0]
    g = image[..., 1]
    b = image[..., 2]

    maximum = np.max(image, axis=2)
    minimum = np.min(image, axis=2)
    chroma = maximum - minimum

    hue = np.zeros_like(maximum)
    nonzero = chroma > 1e-7

    red_max = nonzero & (maximum == r)
    green_max = nonzero & (maximum == g)
    blue_max = nonzero & (maximum == b)

    hue[red_max] = ((g[red_max] - b[red_max]) / chroma[red_max]) % 6.0
    hue[green_max] = ((b[green_max] - r[green_max]) / chroma[green_max]) + 2.0
    hue[blue_max] = ((r[blue_max] - g[blue_max]) / chroma[blue_max]) + 4.0
    hue = hue / 6.0

    saturation = np.zeros_like(maximum)
    nonblack = maximum > 1e-7
    saturation[nonblack] = chroma[nonblack] / maximum[nonblack]

    value = maximum
    return np.stack([hue, saturation, value], axis=2)


def normalize_vector(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float32)
    mean = values.mean(axis=0, keepdims=True)
    std = values.std(axis=0, keepdims=True)
    std = np.where(std < 1e-6, 1.0, std)
    return (values - mean) / std
