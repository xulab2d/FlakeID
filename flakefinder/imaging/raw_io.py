from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import tifffile


def supported_image_files() -> set[str]:
    return {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".npy"}


def load_image(path: str | Path) -> np.ndarray:
    image_path = Path(path)
    suffix = image_path.suffix.lower()
    if suffix == ".npy":
        return np.load(image_path)
    if suffix in {".tif", ".tiff"}:
        return tifffile.imread(image_path)
    image = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise FileNotFoundError(f"Failed to load image: {image_path}")
    return image


def save_image(path: str | Path, image: np.ndarray) -> None:
    image_path = Path(path)
    image_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = image_path.suffix.lower()
    if suffix == ".npy":
        np.save(image_path, image)
        return
    if suffix in {".tif", ".tiff"}:
        tifffile.imwrite(image_path, image)
        return
    cv2.imwrite(str(image_path), image)
