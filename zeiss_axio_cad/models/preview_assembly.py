from __future__ import annotations

import cadquery as cq

from zeiss_axio_cad.models.brackets import build_focus_motor_bracket, build_stage_dual_motor_bracket
from zeiss_axio_cad.models.focus_pulley import build_focus_conical_clamp_pulley
from zeiss_axio_cad.models.split_pulley import build_split_pulley
from zeiss_axio_cad.params import FOCUS, FOCUS_MOUNT, STAGE_STACK, X_STAGE, Y_STAGE


def _assembly_child_shape(asm: cq.Assembly, child_name: str):
    for child in asm.children:
        if child.name == child_name:
            return child.obj
    raise KeyError(child_name)


def build_preview_assembly() -> cq.Assembly:
    stage_bracket = build_stage_dual_motor_bracket(STAGE_STACK)
    focus_bracket = build_focus_motor_bracket(FOCUS_MOUNT)
    x_pulley = build_split_pulley(X_STAGE, "x_stage_split_pulley")
    y_pulley = build_split_pulley(Y_STAGE, "y_stage_split_pulley")
    focus_pulley = build_focus_conical_clamp_pulley(FOCUS)

    asm = cq.Assembly(name="zeiss_axio_preview")

    asm.add(stage_bracket, name="stage_dual_motor_bracket")
    asm.add(
        focus_bracket.translate((-180.0, 0.0, 0.0)),
        name="focus_motor_bracket",
    )

    xz = -STAGE_STACK.center_spacing_mm / 2.0
    yz = STAGE_STACK.center_spacing_mm / 2.0
    stage_pulley_x = -55.0

    asm.add(
        _assembly_child_shape(x_pulley, "left_half").translate((stage_pulley_x - 20.0, 0.0, xz)),
        name="x_stage_pulley_left",
    )
    asm.add(
        _assembly_child_shape(x_pulley, "right_half").translate((stage_pulley_x + 20.0, 0.0, xz)),
        name="x_stage_pulley_right",
    )
    asm.add(
        _assembly_child_shape(y_pulley, "left_half").translate((stage_pulley_x - 24.0, 0.0, yz)),
        name="y_stage_pulley_left",
    )
    asm.add(
        _assembly_child_shape(y_pulley, "right_half").translate((stage_pulley_x + 24.0, 0.0, yz)),
        name="y_stage_pulley_right",
    )

    focus_pulley_x = -120.0
    asm.add(
        _assembly_child_shape(focus_pulley, "left_half").translate((focus_pulley_x - 26.0, 0.0, 0.0)),
        name="focus_pulley_left",
    )
    asm.add(
        _assembly_child_shape(focus_pulley, "right_half").translate((focus_pulley_x + 26.0, 0.0, 0.0)),
        name="focus_pulley_right",
    )
    return asm
