from __future__ import annotations

import numpy as np

from ..utils import rgb_to_hsv


def _bbox_from_mask(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask)
    x0 = int(xs.min())
    x1 = int(xs.max()) + 1
    y0 = int(ys.min())
    y1 = int(ys.max()) + 1
    return x0, y0, x1 - x0, y1 - y0


def _perimeter(mask: np.ndarray) -> int:
    center = mask
    up = np.roll(mask, -1, axis=0)
    down = np.roll(mask, 1, axis=0)
    left = np.roll(mask, -1, axis=1)
    right = np.roll(mask, 1, axis=1)
    edge = center & (~up | ~down | ~left | ~right)
    return int(edge.sum())


def component_feature_vector(image: np.ndarray, mask: np.ndarray, component_score: float) -> dict[str, float]:
    pixels = image[mask]
    hsv_pixels = rgb_to_hsv(pixels.reshape(-1, 1, 3)).reshape(-1, 3)
    luminance = np.mean(pixels, axis=1)
    bbox = _bbox_from_mask(mask)
    area = int(mask.sum())
    perimeter = max(_perimeter(mask), 1)
    fill_ratio = area / max(bbox[2] * bbox[3], 1)

    return {
        "mean_r": float(np.mean(pixels[:, 0])),
        "mean_g": float(np.mean(pixels[:, 1])),
        "mean_b": float(np.mean(pixels[:, 2])),
        "std_r": float(np.std(pixels[:, 0])),
        "std_g": float(np.std(pixels[:, 1])),
        "std_b": float(np.std(pixels[:, 2])),
        "mean_h": float(np.mean(hsv_pixels[:, 0])),
        "mean_s": float(np.mean(hsv_pixels[:, 1])),
        "mean_v": float(np.mean(hsv_pixels[:, 2])),
        "std_luma": float(np.std(luminance)),
        "fill_ratio": float(fill_ratio),
        "compactness": float((perimeter * perimeter) / max(area, 1)),
        "score": float(component_score),
    }

