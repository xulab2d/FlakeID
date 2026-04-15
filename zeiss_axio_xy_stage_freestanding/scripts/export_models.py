from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("XDG_CACHE_HOME", str(REPO_ROOT / ".cache"))

import cadquery as cq
from cadquery import exporters

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from zeiss_axio_cad.models.split_pulley import build_split_pulley
from zeiss_axio_xy_stage_freestanding.models import build_motor_plate, build_pod_ballast_lid, build_pod_body, build_preview
from zeiss_axio_xy_stage_freestanding.params import POD, X_PULLEY, Y_PULLEY


ROOT = Path(__file__).resolve().parents[1]
EXPORT_STL = ROOT / "exports" / "stl"
DONOR_STL = ROOT / "references" / "donor_stl"


def _ensure_dirs() -> None:
    EXPORT_STL.mkdir(parents=True, exist_ok=True)
    DONOR_STL.mkdir(parents=True, exist_ok=True)


def _export_shape(name: str, shape: cq.Shape) -> None:
    exporters.export(shape, str(EXPORT_STL / f"{name}.stl"))


def _export_assembly_children(prefix: str, asm: cq.Assembly) -> None:
    for child in asm.children:
        shape = child.obj if hasattr(child, "obj") else None
        if shape is None:
            continue
        _export_shape(f"{prefix}_{child.name}", shape)


def _copy_donor_refs() -> None:
    donors = [
        REPO_ROOT / "donor_cad" / "uc2_motorized_xy_table" / "stl" / "Assembly_XYTable_Aliepexress_30_XYTable_Aliexpress_motormount_4.stl",
        REPO_ROOT / "donor_cad" / "uc2_motorized_xy_table" / "stl" / "Assembly_XYTable_Aliepexress_00_XYTable_large_gear_29.stl",
        REPO_ROOT / "donor_cad" / "uc2_motorized_xy_table" / "stl" / "Assembly_XYTable_Aliepexress_00_XYTable_medium_gear_27.stl",
        REPO_ROOT / "donor_cad" / "uc2_motorized_xy_table" / "stl" / "Assembly_XYTable_Aliepexress_00_XYTable_pulley_28.stl",
        REPO_ROOT / "donor_cad" / "uc2_micronstage" / "stl" / "Assembly_XY_stage_with_motors_v3_cellSTORM_UC2_motorized_micrometer_motormount_1.stl",
    ]
    for donor in donors:
        if donor.exists():
            shutil.copy2(donor, DONOR_STL / donor.name)


def main() -> int:
    _ensure_dirs()

    x_pulley = build_split_pulley(X_PULLEY, "axio_x_knob_pulley")
    y_pulley = build_split_pulley(Y_PULLEY, "axio_y_knob_pulley")
    pod_body = build_pod_body(POD)
    pod_lid = build_pod_ballast_lid(POD)
    pod_motor_plate = build_motor_plate(POD)
    x_preview = build_preview(POD, 94.0)
    y_preview = build_preview(POD, 120.0)

    _export_assembly_children("axio_x_knob_pulley", x_pulley)
    _export_assembly_children("axio_y_knob_pulley", y_pulley)
    _export_shape("xy_pod_body", pod_body)
    _export_shape("xy_pod_ballast_lid", pod_lid)
    _export_shape("xy_pod_motor_plate_nema17", pod_motor_plate)
    _export_assembly_children("x_drive_preview", x_preview)
    _export_assembly_children("y_drive_preview", y_preview)
    _copy_donor_refs()
    print(f"Exported STLs to {EXPORT_STL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
