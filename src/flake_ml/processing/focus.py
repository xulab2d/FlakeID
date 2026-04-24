from __future__ import annotations

from pathlib import Path

import numpy as np

from .preprocess import load_image


def _to_grayscale(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image.astype(np.float32)
    if image.ndim != 3 or image.shape[2] < 3:
        raise ValueError("Focus metrics expect a grayscale or RGB image array.")
    rgb = image[..., :3].astype(np.float32)
    return 0.2989 * rgb[..., 0] + 0.5870 * rgb[..., 1] + 0.1140 * rgb[..., 2]


def _crop_center(image: np.ndarray, crop_fraction: float) -> np.ndarray:
    if crop_fraction >= 1.0:
        return image
    if crop_fraction <= 0.0:
        raise ValueError("crop_fraction must be positive.")
    height, width = image.shape[:2]
    crop_height = max(8, int(round(height * crop_fraction)))
    crop_width = max(8, int(round(width * crop_fraction)))
    y0 = max(0, (height - crop_height) // 2)
    x0 = max(0, (width - crop_width) // 2)
    return image[y0:y0 + crop_height, x0:x0 + crop_width]


def variance_of_laplacian(gray: np.ndarray) -> float:
    center = gray[1:-1, 1:-1]
    lap = (
        -4.0 * center
        + gray[:-2, 1:-1]
        + gray[2:, 1:-1]
        + gray[1:-1, :-2]
        + gray[1:-1, 2:]
    )
    return float(np.var(lap))


def tenengrad(gray: np.ndarray) -> float:
    gx = (
        -gray[:-2, :-2] - 2.0 * gray[1:-1, :-2] - gray[2:, :-2]
        + gray[:-2, 2:] + 2.0 * gray[1:-1, 2:] + gray[2:, 2:]
    )
    gy = (
        -gray[:-2, :-2] - 2.0 * gray[:-2, 1:-1] - gray[:-2, 2:]
        + gray[2:, :-2] + 2.0 * gray[2:, 1:-1] + gray[2:, 2:]
    )
    return float(np.mean(gx * gx + gy * gy))


def brenner(gray: np.ndarray) -> float:
    dx = gray[:, 2:] - gray[:, :-2]
    dy = gray[2:, :] - gray[:-2, :]
    return float(np.mean(dx * dx) + np.mean(dy * dy))


def normalized_variance(gray: np.ndarray) -> float:
    mean = float(np.mean(gray))
    if mean <= 1e-8:
        return 0.0
    return float(np.var(gray) / mean)


def focus_metrics(image: np.ndarray, crop_fraction: float = 1.0) -> dict[str, float]:
    gray = _to_grayscale(image)
    gray = _crop_center(gray, crop_fraction=crop_fraction)
    return {
        "variance_of_laplacian": variance_of_laplacian(gray),
        "tenengrad": tenengrad(gray),
        "brenner": brenner(gray),
        "normalized_variance": normalized_variance(gray),
    }


def focus_metrics_for_path(path: str | Path, crop_fraction: float = 1.0) -> dict[str, float]:
    image = load_image(path)
    metrics = focus_metrics(image, crop_fraction=crop_fraction)
    metrics["image_path"] = str(Path(path).resolve())
    return metrics
