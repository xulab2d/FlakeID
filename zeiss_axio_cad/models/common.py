from __future__ import annotations

import cadquery as cq


def hex_cut(width_across_flats_mm: float, height_mm: float) -> cq.Workplane:
    radius = width_across_flats_mm / 1.7320508075688772
    return (
        cq.Workplane("XY")
        .polygon(6, radius * 2.0)
        .extrude(height_mm)
    )
