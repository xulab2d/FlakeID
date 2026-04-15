from __future__ import annotations

import cadquery as cq

from zeiss_axio_xy_stage_freestanding.params import FreestandingPodParams


def build_pod_body(params: FreestandingPodParams) -> cq.Workplane:
    base = (
        cq.Workplane("XY")
        .rect(params.base_length_mm, params.base_width_mm)
        .extrude(params.base_height_mm)
    )

    cavity = (
        cq.Workplane("XY")
        .center(0.0, 6.0)
        .rect(params.ballast_cavity_length_mm, params.ballast_cavity_width_mm)
        .extrude(params.ballast_cavity_depth_mm)
        .translate((0.0, 0.0, params.base_height_mm - params.ballast_cavity_depth_mm))
    )
    body = base.cut(cavity)

    tower = (
        cq.Workplane("XY")
        .center(0.0, -(params.base_width_mm / 2.0) + (params.tower_thickness_mm / 2.0))
        .rect(params.tower_width_mm, params.tower_thickness_mm)
        .extrude(params.base_height_mm + params.tower_height_mm)
    )
    body = body.union(tower)

    access_window = (
        cq.Workplane("XZ")
        .center(0.0, params.base_height_mm + params.access_window_z_center_mm)
        .rect(params.access_window_width_mm, params.access_window_height_mm)
        .extrude(params.tower_thickness_mm + 2.0)
        .translate((0.0, -(params.base_width_mm / 2.0) - 1.0, 0.0))
    )
    body = body.cut(access_window)

    slot_centers = [
        (-params.slot_center_spacing_mm / 2.0, params.slot_z_center_mm),
        (params.slot_center_spacing_mm / 2.0, params.slot_z_center_mm),
    ]
    slots = (
        cq.Workplane("XZ")
        .center(0.0, params.base_height_mm)
        .pushPoints(slot_centers)
        .slot2D(params.slot_height_mm, params.slot_width_mm, 90.0)
        .extrude(params.tower_thickness_mm + 2.0)
        .translate((0.0, -(params.base_width_mm / 2.0) - 1.0, 0.0))
    )
    body = body.cut(slots)

    cable_notch = (
        cq.Workplane("XZ")
        .center(0.0, params.base_height_mm + params.tower_height_mm - (params.cable_notch_depth_mm / 2.0))
        .rect(params.cable_notch_width_mm, params.cable_notch_depth_mm)
        .extrude(params.tower_thickness_mm + 2.0)
        .translate((0.0, -(params.base_width_mm / 2.0) - 1.0, 0.0))
    )
    body = body.cut(cable_notch)

    tie_slots = (
        cq.Workplane("XZ")
        .center(0.0, params.base_height_mm)
        .pushPoints(
            [
                (-params.cable_tie_slot_x_spacing_mm / 2.0, params.cable_tie_slot_z_mm),
                (params.cable_tie_slot_x_spacing_mm / 2.0, params.cable_tie_slot_z_mm),
            ]
        )
        .slot2D(params.cable_tie_slot_height_mm, params.cable_tie_slot_width_mm, 90.0)
        .extrude(params.tower_thickness_mm + 2.0)
        .translate((0.0, -(params.base_width_mm / 2.0) - 1.0, 0.0))
    )
    body = body.cut(tie_slots)

    finger_cut = (
        cq.Workplane("XY")
        .center(0.0, 6.0)
        .pushPoints([(-26.0, 0.0), (26.0, 0.0)])
        .circle(9.0)
        .extrude(params.base_height_mm + 2.0)
        .translate((0.0, 0.0, params.base_height_mm - params.ballast_cavity_depth_mm - 1.0))
    )
    body = body.cut(finger_cut)
    return body


def build_pod_ballast_lid(params: FreestandingPodParams) -> cq.Workplane:
    lid = (
        cq.Workplane("XY")
        .rect(params.ballast_cavity_length_mm + 6.0, params.ballast_cavity_width_mm + 6.0)
        .extrude(params.lid_thickness_mm)
    )
    lip = (
        cq.Workplane("XY")
        .rect(params.ballast_cavity_length_mm - 3.0, params.ballast_cavity_width_mm - 3.0)
        .extrude(params.lid_thickness_mm)
        .translate((0.0, 0.0, -params.lid_lip_mm))
    )
    finger_holes = (
        cq.Workplane("XY")
        .pushPoints([(-24.0, 0.0), (24.0, 0.0)])
        .circle(7.0)
        .extrude(params.lid_thickness_mm + params.lid_lip_mm + 1.0)
        .translate((0.0, 0.0, -params.lid_lip_mm - 0.5))
    )
    return lid.union(lip).cut(finger_holes)


def build_motor_plate(params: FreestandingPodParams) -> cq.Workplane:
    plate = (
        cq.Workplane("XY")
        .box(
            params.motor_plate_width_mm,
            params.motor_plate_depth_mm,
            params.motor_plate_thickness_mm,
            centered=(True, True, False),
        )
    )

    flange = (
        cq.Workplane("XY")
        .center(0.0, -(params.motor_plate_depth_mm / 2.0) + (params.motor_plate_flange_thickness_mm / 2.0))
        .box(
            params.motor_plate_width_mm,
            params.motor_plate_flange_thickness_mm,
            params.motor_plate_flange_height_mm,
            centered=(True, True, False),
        )
    )
    plate = plate.union(flange)

    motor_holes = (
        cq.Workplane("XY")
        .workplane(offset=-0.5)
        .pushPoints(
            [
                (-params.motor_mount_hole_spacing_mm / 2.0, -params.motor_mount_hole_spacing_mm / 2.0),
                (params.motor_mount_hole_spacing_mm / 2.0, -params.motor_mount_hole_spacing_mm / 2.0),
                (-params.motor_mount_hole_spacing_mm / 2.0, params.motor_mount_hole_spacing_mm / 2.0),
                (params.motor_mount_hole_spacing_mm / 2.0, params.motor_mount_hole_spacing_mm / 2.0),
            ]
        )
        .circle(params.motor_mount_hole_d_mm / 2.0)
        .extrude(params.motor_plate_thickness_mm + 2.0)
    )
    shaft_hole = (
        cq.Workplane("XY")
        .workplane(offset=-0.5)
        .circle(params.motor_center_hole_d_mm / 2.0)
        .extrude(params.motor_plate_thickness_mm + 2.0)
    )
    cable_slot = (
        cq.Workplane("XY")
        .center(0.0, (params.motor_center_hole_d_mm / 4.0) + (params.motor_cable_slot_length_mm / 2.0))
        .slot2D(params.motor_cable_slot_length_mm, params.motor_cable_slot_width_mm, 0.0)
        .extrude(params.motor_plate_thickness_mm + 2.0)
        .translate((0.0, 0.0, -0.5))
    )
    plate = plate.cut(motor_holes).cut(shaft_hole).cut(cable_slot)

    tower_holes = (
        cq.Workplane("XZ")
        .center(0.0, params.motor_plate_flange_height_mm / 2.0)
        .pushPoints(
            [
                (-params.tower_mount_hole_spacing_mm / 2.0, 0.0),
                (params.tower_mount_hole_spacing_mm / 2.0, 0.0),
            ]
        )
        .circle(params.tower_mount_hole_d_mm / 2.0)
        .extrude(params.motor_plate_flange_thickness_mm + 2.0)
        .translate((0.0, -(params.motor_plate_depth_mm / 2.0) - 1.0, 0.0))
    )
    plate = plate.cut(tower_holes)

    tie_slots = (
        cq.Workplane("XZ")
        .center(0.0, params.motor_plate_flange_height_mm * 0.72)
        .pushPoints([(-14.0, 0.0), (14.0, 0.0)])
        .slot2D(12.0, 4.5, 90.0)
        .extrude(params.motor_plate_flange_thickness_mm + 2.0)
        .translate((0.0, -(params.motor_plate_depth_mm / 2.0) - 1.0, 0.0))
    )
    plate = plate.cut(tie_slots)
    return plate


def build_preview(params: FreestandingPodParams, plate_z_mm: float) -> cq.Assembly:
    asm = cq.Assembly()
    body = build_pod_body(params)
    plate = build_motor_plate(params).translate((0.0, -(params.base_width_mm / 2.0) - (params.motor_plate_depth_mm / 2.0) - 2.0, plate_z_mm))
    lid = build_pod_ballast_lid(params).translate((0.0, 6.0, params.base_height_mm - params.lid_thickness_mm))
    asm.add(body, name="body")
    asm.add(lid, name="lid")
    asm.add(plate, name="motor_plate")
    return asm
