from __future__ import annotations

import math

from flakefinder.config.models import AppConfig

from .planner import ScanTile, tile_step_mm


def generate_serpentine_tiles(config: AppConfig) -> list[ScanTile]:
    roi = config.hardware.roi
    step_x, step_y = tile_step_mm(config)
    cols = max(1, math.ceil(roi.width_mm / step_x))
    rows = max(1, math.ceil(roi.height_mm / step_y))
    tiles: list[ScanTile] = []
    tile_index = 0
    for row in range(rows):
        direction = range(cols) if row % 2 == 0 else range(cols - 1, -1, -1)
        for col in direction:
            x_mm = roi.x_mm + col * step_x
            y_mm = roi.y_mm + row * step_y
            tiles.append(ScanTile(tile_index=tile_index, row=row, col=col, x_mm=x_mm, y_mm=y_mm))
            tile_index += 1
    return tiles
