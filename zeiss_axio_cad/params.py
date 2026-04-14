from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FocusParams:
    knob_d_end_mm: float = 34.12
    knob_d_base_mm: float = 37.52
    knob_height_mm: float = 26.5
    bore_clearance_mm: float = 0.4
    outer_d_mm: float = 54.0
    body_height_mm: float = 30.0
    wall_mm: float = 5.0
    split_gap_mm: float = 1.2
    ear_width_mm: float = 10.0
    ear_depth_mm: float = 8.0
    clamp_hole_d_mm: float = 3.4
    clamp_hole_spacing_mm: float = 11.0


@dataclass(frozen=True, slots=True)
class StageStackParams:
    x_knob_d_mm: float = 27.8
    y_knob_d_mm: float = 32.93
    center_spacing_mm: float = 32.0
    y_on_top: bool = True
    shaft_orientation: str = "vertical"
    belt_exit_direction: str = "right"
    pulley_to_motor_offset_mm: float = 70.0
    motor_face_size_mm: float = 42.3
    motor_mount_hole_spacing_mm: float = 31.0
    motor_mount_hole_d_mm: float = 3.4
    bracket_plate_thickness_mm: float = 6.0
    bracket_plate_width_mm: float = 70.0
    bracket_plate_height_mm: float = 120.0
    standoff_depth_mm: float = 24.0


@dataclass(frozen=True, slots=True)
class FocusMountParams:
    motor_face_size_mm: float = 35.0
    motor_mount_hole_spacing_mm: float = 26.0
    motor_mount_hole_d_mm: float = 3.4
    pulley_to_motor_offset_mm: float = 65.0
    bracket_plate_thickness_mm: float = 6.0
    bracket_plate_width_mm: float = 65.0
    bracket_plate_height_mm: float = 90.0
    standoff_depth_mm: float = 24.0


@dataclass(frozen=True, slots=True)
class SplitPulleyParams:
    knob_d_mm: float
    outer_d_mm: float
    flange_height_mm: float = 18.0
    body_height_mm: float = 24.0
    bore_clearance_mm: float = 0.5
    split_gap_mm: float = 1.0
    ear_width_mm: float = 9.0
    ear_depth_mm: float = 8.0
    clamp_hole_d_mm: float = 3.4
    clamp_hole_spacing_mm: float = 9.0


FOCUS = FocusParams()
X_STAGE = SplitPulleyParams(knob_d_mm=27.8, outer_d_mm=44.0)
Y_STAGE = SplitPulleyParams(knob_d_mm=32.93, outer_d_mm=50.0)
STAGE_STACK = StageStackParams()
FOCUS_MOUNT = FocusMountParams()
