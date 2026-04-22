from __future__ import annotations

from math import ceil

from ..models import ScanTile, StagePosition


def _count_tiles(extent_um: float, fov_um: float, overlap_fraction: float) -> int:
    if extent_um <= fov_um:
        return 1
    step_um = fov_um * (1.0 - overlap_fraction)
    return int(ceil((extent_um - fov_um) / step_um)) + 1


def build_serpentine_plan(
    width_um: float,
    height_um: float,
    fov_width_um: float,
    fov_height_um: float,
    overlap_fraction: float,
    origin_x_um: float = 0.0,
    origin_y_um: float = 0.0,
) -> list[ScanTile]:
    columns = _count_tiles(width_um, fov_width_um, overlap_fraction)
    rows = _count_tiles(height_um, fov_height_um, overlap_fraction)
    step_x = fov_width_um * (1.0 - overlap_fraction)
    step_y = fov_height_um * (1.0 - overlap_fraction)

    tiles: list[ScanTile] = []
    tile_index = 0
    for row in range(rows):
        y_um = origin_y_um + row * step_y
        column_order = range(columns) if row % 2 == 0 else range(columns - 1, -1, -1)
        for column in column_order:
            x_um = origin_x_um + column * step_x
            tiles.append(
                ScanTile(
                    index=tile_index,
                    row=row,
                    column=column,
                    position=StagePosition(x_um=x_um, y_um=y_um),
                    width_um=fov_width_um,
                    height_um=fov_height_um,
                    overlap_fraction=overlap_fraction,
                )
            )
            tile_index += 1
    return tiles

