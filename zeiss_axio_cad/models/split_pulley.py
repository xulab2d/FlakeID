from __future__ import annotations

import cadquery as cq

from zeiss_axio_cad.params import SplitPulleyParams


def build_split_pulley(params: SplitPulleyParams, assembly_name: str) -> cq.Assembly:
    main_body = cq.Workplane("XY").circle((params.outer_d_mm - 4.0) / 2.0).extrude(params.body_height_mm)
    flange = (
        cq.Workplane("XY")
        .circle(params.outer_d_mm / 2.0)
        .extrude(params.flange_height_mm)
        .translate((0, 0, (params.body_height_mm - params.flange_height_mm) / 2.0))
    )
    bore = cq.Workplane("XY").circle((params.knob_d_mm + params.bore_clearance_mm) / 2.0).extrude(params.body_height_mm + 2.0)
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
    split_slot = (
        cq.Workplane("XY")
        .box(params.outer_d_mm + 20.0, params.split_gap_mm, params.body_height_mm + 2.0)
        .translate((0, 0, params.body_height_mm / 2.0))
    )

    body = main_body.union(flange).union(ears).cut(bore.translate((0, 0, -1.0))).cut(split_slot)

    for z_frac in (0.35, 0.7):
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

    asm = cq.Assembly(name=assembly_name)
    asm.add(left_half.translate((-params.outer_d_mm * 0.7, 0, 0)), name="left_half")
    asm.add(right_half.translate((params.outer_d_mm * 0.7, 0, 0)), name="right_half")
    return asm
