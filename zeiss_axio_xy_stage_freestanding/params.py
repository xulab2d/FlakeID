from __future__ import annotations

from dataclasses import dataclass

from zeiss_axio_cad.params import SplitPulleyParams


@dataclass(frozen=True, slots=True)
class MeasuredHeights:
    x_knob_bottom_from_table_mm: float = 85.0
    y_knob_bottom_from_table_mm: float = 109.0
    stage_bottom_from_table_mm: float = 180.0


@dataclass(frozen=True, slots=True)
class FreestandingPodParams:
    base_length_mm: float = 150.0
    base_width_mm: float = 90.0
    base_height_mm: float = 28.0
    base_wall_mm: float = 4.0
    ballast_cavity_length_mm: float = 110.0
    ballast_cavity_width_mm: float = 56.0
    ballast_cavity_depth_mm: float = 20.0
    lid_thickness_mm: float = 3.0
    lid_lip_mm: float = 1.4
    tower_width_mm: float = 78.0
    tower_thickness_mm: float = 12.0
    tower_height_mm: float = 150.0
    slot_width_mm: float = 6.6
    slot_height_mm: float = 70.0
    slot_center_spacing_mm: float = 38.0
    slot_z_center_mm: float = 82.0
    motor_plate_width_mm: float = 80.0
    motor_plate_depth_mm: float = 76.0
    motor_plate_thickness_mm: float = 6.0
    motor_plate_flange_height_mm: float = 42.0
    motor_plate_flange_thickness_mm: float = 8.0
    motor_mount_hole_spacing_mm: float = 31.0
    motor_mount_hole_d_mm: float = 3.4
    motor_center_hole_d_mm: float = 23.0
    tower_mount_hole_d_mm: float = 5.4
    tower_mount_hole_spacing_mm: float = 38.0


HEIGHTS = MeasuredHeights()
POD = FreestandingPodParams()
X_PULLEY = SplitPulleyParams(knob_d_mm=27.8, outer_d_mm=44.0, body_height_mm=20.0, flange_height_mm=14.0)
Y_PULLEY = SplitPulleyParams(knob_d_mm=32.93, outer_d_mm=50.0, body_height_mm=20.0, flange_height_mm=14.0)
