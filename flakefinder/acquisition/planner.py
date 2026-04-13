from __future__ import annotations

from dataclasses import dataclass

from flakefinder.config.models import AppConfig


@dataclass(slots=True)
class ScanTile:
    tile_index: int
    row: int
    col: int
    x_mm: float
    y_mm: float


def tile_step_mm(config: AppConfig) -> tuple[float, float]:
    frame_w_mm = (config.hardware.frame_width_px * config.hardware.pixel_size_um) / 1000.0
    frame_h_mm = (config.hardware.frame_height_px * config.hardware.pixel_size_um) / 1000.0
    step_x = frame_w_mm * (1.0 - config.hardware.overlap)
    step_y = frame_h_mm * (1.0 - config.hardware.overlap)
    return step_x, step_y
