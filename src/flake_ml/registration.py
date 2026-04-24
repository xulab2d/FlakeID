from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .processing.preprocess import load_image


@dataclass(slots=True)
class ShiftEstimate:
    dx_px: float
    dy_px: float
    peak: float
    crop_width_px: int
    crop_height_px: int

    def to_dict(self) -> dict[str, float | int]:
        return {
            "dx_px": self.dx_px,
            "dy_px": self.dy_px,
            "peak": self.peak,
            "crop_width_px": self.crop_width_px,
            "crop_height_px": self.crop_height_px,
        }


def _to_luma(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image.astype(np.float32)
    rgb = image[..., :3].astype(np.float32)
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


def phase_correlation_shift(reference: np.ndarray, moving: np.ndarray) -> ShiftEstimate:
    ref = _to_luma(reference)
    mov = _to_luma(moving)
    if ref.shape != mov.shape:
        raise ValueError("Reference and moving images must have the same shape.")

    height, width = ref.shape
    window_y = np.hanning(height).astype(np.float32)
    window_x = np.hanning(width).astype(np.float32)
    window = np.outer(window_y, window_x)

    ref_windowed = (ref - np.mean(ref)) * window
    mov_windowed = (mov - np.mean(mov)) * window

    ref_fft = np.fft.fft2(ref_windowed)
    mov_fft = np.fft.fft2(mov_windowed)
    cross_power = ref_fft * np.conj(mov_fft)
    cross_power /= np.maximum(np.abs(cross_power), 1e-9)
    correlation = np.fft.ifft2(cross_power)
    magnitude = np.abs(correlation)
    peak_index = np.unravel_index(np.argmax(magnitude), magnitude.shape)

    shift_y = float(peak_index[0])
    shift_x = float(peak_index[1])
    if shift_y > height / 2:
        shift_y -= height
    if shift_x > width / 2:
        shift_x -= width

    return ShiftEstimate(
        dx_px=shift_x,
        dy_px=shift_y,
        peak=float(magnitude[peak_index]),
        crop_width_px=width,
        crop_height_px=height,
    )


def estimate_overlap_shift(
    reference: np.ndarray,
    moving: np.ndarray,
    axis: str,
    overlap_fraction: float,
) -> ShiftEstimate:
    ref = _to_luma(reference)
    mov = _to_luma(moving)
    if ref.shape != mov.shape:
        raise ValueError("Reference and moving images must have the same shape.")
    if not 0.0 < overlap_fraction < 1.0:
        raise ValueError("overlap_fraction must be between 0 and 1.")

    height, width = ref.shape
    if axis == "x":
        crop_width = max(8, int(round(width * overlap_fraction)))
        ref_crop = ref[:, width - crop_width :]
        mov_crop = mov[:, :crop_width]
    elif axis == "y":
        crop_height = max(8, int(round(height * overlap_fraction)))
        ref_crop = ref[height - crop_height :, :]
        mov_crop = mov[:crop_height, :]
    else:
        raise ValueError("axis must be 'x' or 'y'.")

    return phase_correlation_shift(ref_crop, mov_crop)


def estimate_overlap_shift_from_paths(
    reference_path: str | Path,
    moving_path: str | Path,
    axis: str,
    overlap_fraction: float,
) -> ShiftEstimate:
    reference = load_image(reference_path)
    moving = load_image(moving_path)
    return estimate_overlap_shift(reference, moving, axis=axis, overlap_fraction=overlap_fraction)
