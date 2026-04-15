from __future__ import annotations

import cadquery as cq

from zeiss_axio_cad.models.common import hex_cut
from zeiss_axio_xy_stage_freestanding.params import CompliantClampPulleyParams


def _half_boxes(params: CompliantClampPulleyParams) -> tuple[cq.Workplane, cq.Workplane]:
    envelope = params.outer_d_mm + 50.0
    half_width = envelope / 2.0
    left_box = (
        cq.Workplane("XY")
        .box(half_width, envelope, params.body_height_mm + 6.0)
        .translate((-(half_width / 2.0), 0.0, params.body_height_mm / 2.0))
    )
    right_box = (
        cq.Workplane("XY")
        .box(half_width, envelope, params.body_height_mm + 6.0)
        .translate(((half_width / 2.0), 0.0, params.body_height_mm / 2.0))
    )
    return left_box, right_box


def _rigid_bore_diameter(params: CompliantClampPulleyParams) -> float:
    return params.knob_d_mm + (2.0 * params.liner_nominal_thickness_mm) + params.rigid_bore_clearance_mm


def build_compliant_clamp_pulley(params: CompliantClampPulleyParams, assembly_name: str) -> cq.Assembly:
    rigid_core = cq.Workplane("XY").circle((params.outer_d_mm - 4.0) / 2.0).extrude(params.body_height_mm)
    flange = (
        cq.Workplane("XY")
        .circle(params.outer_d_mm / 2.0)
        .extrude(params.flange_height_mm)
        .translate((0.0, 0.0, (params.body_height_mm - params.flange_height_mm) / 2.0))
    )
    ears = (
        cq.Workplane("XY")
        .pushPoints(
            [
                (params.outer_d_mm / 2.0 + params.ear_width_mm / 2.0 - 1.0, 0.0),
                (-(params.outer_d_mm / 2.0 + params.ear_width_mm / 2.0 - 1.0), 0.0),
            ]
        )
        .box(params.ear_width_mm, params.ear_depth_mm, params.body_height_mm)
        .translate((0.0, 0.0, params.body_height_mm / 2.0))
    )
    rigid = rigid_core.union(flange).union(ears)

    bore = (
        cq.Workplane("XY")
        .circle(_rigid_bore_diameter(params) / 2.0)
        .extrude(params.body_height_mm + 2.0)
        .translate((0.0, 0.0, -1.0))
    )
    split_slot = (
        cq.Workplane("XY")
        .box(params.outer_d_mm + 24.0, params.split_gap_mm, params.body_height_mm + 2.0)
        .translate((0.0, 0.0, params.body_height_mm / 2.0))
    )
    rigid = rigid.cut(bore).cut(split_slot)

    through_len = params.outer_d_mm + (2.0 * params.ear_width_mm) + 24.0
    for z_frac in params.clamp_z_fracs:
        z = params.body_height_mm * z_frac
        hole = (
            cq.Workplane("YZ")
            .center(0.0, z)
            .circle(params.clamp_hole_d_mm / 2.0)
            .extrude(through_len)
            .translate((-(through_len / 2.0), 0.0, 0.0))
        )
        head_pocket = (
            cq.Workplane("YZ")
            .center(0.0, z)
            .circle(params.clamp_head_d_mm / 2.0)
            .extrude(params.clamp_head_depth_mm + 0.2)
            .translate((-(through_len / 2.0) - 0.1, 0.0, 0.0))
        )
        nut_pocket = (
            hex_cut(params.clamp_nut_width_mm, params.clamp_nut_depth_mm + 0.2)
            .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 90.0)
            .rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), 90.0)
            .translate(((through_len / 2.0) - ((params.clamp_nut_depth_mm + 0.2) / 2.0) + 0.1, 0.0, z))
        )
        rigid = rigid.cut(hole).cut(head_pocket).cut(nut_pocket)

    left_box, right_box = _half_boxes(params)
    rigid_left = rigid.intersect(left_box)
    rigid_right = rigid.intersect(right_box)

    asm = cq.Assembly(name=assembly_name)
    sep = params.outer_d_mm * 0.62
    asm.add(rigid_left.translate((-sep, 0.0, 0.0)), name="left_half")
    asm.add(rigid_right.translate((sep, 0.0, 0.0)), name="right_half")
    return asm
