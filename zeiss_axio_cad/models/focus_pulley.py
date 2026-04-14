from __future__ import annotations

import cadquery as cq

from zeiss_axio_cad.params import FocusParams


def build_focus_conical_clamp_pulley(params: FocusParams) -> cq.Assembly:
    outer = cq.Workplane("XY").circle(params.outer_d_mm / 2.0).extrude(params.body_height_mm)
    taper = (
        cq.Workplane("XY")
        .circle((params.knob_d_base_mm + params.bore_clearance_mm) / 2.0)
        .workplane(offset=params.knob_height_mm)
        .circle((params.knob_d_end_mm + params.bore_clearance_mm) / 2.0)
        .loft(combine=True)
    )
    split_slot = (
        cq.Workplane("XY")
        .box(params.outer_d_mm + 20.0, params.split_gap_mm, params.body_height_mm + 2.0)
        .translate((0, 0, params.body_height_mm / 2.0))
    )
    ears = (
        cq.Workplane("XY")
        .pushPoints(
            [
                (params.outer_d_mm / 2.0 + params.ear_width_mm / 2.0 - 1.0, 0),
                (-(params.outer_d_mm / 2.0 + params.ear_width_mm / 2.0 - 1.0), 0),
            ]
        )
        .box(params.ear_width_mm, params.ear_depth_mm, params.body_height_mm)
        .translate((0, 0, params.body_height_mm / 2.0))
    )
    body = outer.union(ears).cut(taper.translate((0, 0, 1.0))).cut(split_slot)

    for z_frac in (0.33, 0.66):
        z = params.body_height_mm * z_frac
        hole = (
            cq.Workplane("YZ")
            .center(0, z)
            .circle(params.clamp_hole_d_mm / 2.0)
            .extrude(params.outer_d_mm + params.ear_width_mm * 2.0 + 20.0)
        )
        body = body.cut(hole)

    left_half = body.intersect(
        cq.Workplane("XY")
        .box(params.outer_d_mm + 40.0, params.outer_d_mm + 40.0, params.body_height_mm + 4.0)
        .translate((-(params.outer_d_mm + 40.0) / 4.0, 0, params.body_height_mm / 2.0))
    )
    right_half = body.intersect(
        cq.Workplane("XY")
        .box(params.outer_d_mm + 40.0, params.outer_d_mm + 40.0, params.body_height_mm + 4.0)
        .translate(((params.outer_d_mm + 40.0) / 4.0, 0, params.body_height_mm / 2.0))
    )

    asm = cq.Assembly(name="focus_conical_clamp_pulley")
    asm.add(left_half.translate((-params.outer_d_mm * 0.7, 0, 0)), name="left_half")
    asm.add(right_half.translate((params.outer_d_mm * 0.7, 0, 0)), name="right_half")
    return asm
