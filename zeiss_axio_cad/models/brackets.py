from __future__ import annotations

import cadquery as cq

from zeiss_axio_cad.params import FocusMountParams, StageStackParams


def _motor_hole_pattern(
    workplane: cq.Workplane,
    center_x: float,
    center_z: float,
    spacing: float,
    hole_d: float,
) -> cq.Workplane:
    return workplane.pushPoints(
        [
            (center_x - spacing / 2.0, center_z - spacing / 2.0),
            (center_x + spacing / 2.0, center_z - spacing / 2.0),
            (center_x - spacing / 2.0, center_z + spacing / 2.0),
            (center_x + spacing / 2.0, center_z + spacing / 2.0),
        ]
    ).circle(hole_d / 2.0)


def build_stage_dual_motor_bracket(params: StageStackParams) -> cq.Workplane:
    plate = (
        cq.Workplane("XZ")
        .rect(params.bracket_plate_width_mm, params.bracket_plate_height_mm)
        .extrude(params.bracket_plate_thickness_mm)
    )
    standoff = (
        cq.Workplane("XZ")
        .center(-(params.bracket_plate_width_mm / 2.0) + 10.0, 0.0)
        .rect(20.0, params.bracket_plate_height_mm)
        .extrude(params.standoff_depth_mm)
    )
    body = plate.union(standoff)

    x_center_z = -params.center_spacing_mm / 2.0
    y_center_z = params.center_spacing_mm / 2.0
    holes = _motor_hole_pattern(
        cq.Workplane("XZ"),
        0.0,
        x_center_z,
        params.motor_mount_hole_spacing_mm,
        params.motor_mount_hole_d_mm,
    )
    holes = _motor_hole_pattern(
        holes,
        0.0,
        y_center_z,
        params.motor_mount_hole_spacing_mm,
        params.motor_mount_hole_d_mm,
    )
    body = body.cut(holes.extrude(params.bracket_plate_thickness_mm + params.standoff_depth_mm + 2.0))
    shaft_windows = (
        cq.Workplane("XZ")
        .pushPoints([(0.0, x_center_z), (0.0, y_center_z)])
        .rect(22.0, 22.0)
        .extrude(params.bracket_plate_thickness_mm + params.standoff_depth_mm + 2.0)
    )
    return body.cut(shaft_windows)


def build_focus_motor_bracket(params: FocusMountParams) -> cq.Workplane:
    plate = (
        cq.Workplane("XZ")
        .rect(params.bracket_plate_width_mm, params.bracket_plate_height_mm)
        .extrude(params.bracket_plate_thickness_mm)
    )
    standoff = (
        cq.Workplane("XZ")
        .center(-(params.bracket_plate_width_mm / 2.0) + 10.0, 0.0)
        .rect(20.0, params.bracket_plate_height_mm)
        .extrude(params.standoff_depth_mm)
    )
    body = plate.union(standoff)
    holes = _motor_hole_pattern(
        cq.Workplane("XZ"),
        0.0,
        0.0,
        params.motor_mount_hole_spacing_mm,
        params.motor_mount_hole_d_mm,
    )
    body = body.cut(holes.extrude(params.bracket_plate_thickness_mm + params.standoff_depth_mm + 2.0))
    shaft_window = (
        cq.Workplane("XZ")
        .rect(18.0, 18.0)
        .extrude(params.bracket_plate_thickness_mm + params.standoff_depth_mm + 2.0)
    )
    return body.cut(shaft_window)
