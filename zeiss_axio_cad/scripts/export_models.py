from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("XDG_CACHE_HOME", str(REPO_ROOT / ".cache"))

import cadquery as cq
from cadquery import exporters

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from zeiss_axio_cad.models import (
    build_focus_conical_clamp_pulley,
    build_focus_motor_bracket,
    build_preview_assembly,
    build_split_pulley,
    build_stage_dual_motor_bracket,
)
from zeiss_axio_cad.params import FOCUS, FOCUS_MOUNT, STAGE_STACK, X_STAGE, Y_STAGE


ROOT = Path(__file__).resolve().parents[1]
EXPORT_STL = ROOT / "exports" / "stl"
EXPORT_STEP = ROOT / "exports" / "step"


def _ensure_dirs() -> None:
    EXPORT_STL.mkdir(parents=True, exist_ok=True)
    EXPORT_STEP.mkdir(parents=True, exist_ok=True)


def _export_shape(name: str, shape: cq.Shape) -> None:
    exporters.export(shape, str(EXPORT_STL / f"{name}.stl"))
    exporters.export(shape, str(EXPORT_STEP / f"{name}.step"))


def _export_assembly_children(prefix: str, asm: cq.Assembly) -> None:
    for child in asm.children:
        shape = child.obj if hasattr(child, "obj") else None
        if shape is None:
            continue
        _export_shape(f"{prefix}_{child.name}", shape)


def main() -> int:
    _ensure_dirs()
    focus_asm = build_focus_conical_clamp_pulley(FOCUS)
    x_asm = build_split_pulley(X_STAGE, "x_stage_split_pulley")
    y_asm = build_split_pulley(Y_STAGE, "y_stage_split_pulley")
    stage_bracket = build_stage_dual_motor_bracket(STAGE_STACK)
    focus_bracket = build_focus_motor_bracket(FOCUS_MOUNT)
    preview = build_preview_assembly()

    for asm_name, asm in [
        ("focus_conical_clamp_pulley", focus_asm),
        ("x_stage_split_pulley", x_asm),
        ("y_stage_split_pulley", y_asm),
    ]:
        _export_assembly_children(asm_name, asm)
    _export_shape("stage_dual_motor_bracket", stage_bracket)
    _export_shape("focus_motor_bracket", focus_bracket)
    _export_assembly_children("preview", preview)
    print(f"Exported models to {EXPORT_STL} and {EXPORT_STEP}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
