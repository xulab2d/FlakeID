from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import json
import shutil

from .config import LabConfig
from .utils import ensure_dir, timestamp_utc


def _session_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def initialize_session(
    output_root: str | Path,
    config_path: str | Path,
    config: LabConfig,
    sample_id: str,
    material: str,
    substrate: str,
    objective: str,
    operator: str = "",
    notes: str = "",
) -> dict:
    timestamp = _session_timestamp()
    session_name = f"{timestamp}_{sample_id}"
    session_dir = ensure_dir(Path(output_root) / session_name)

    subdirs = {
        "incoming": ensure_dir(session_dir / "incoming"),
        "tiles": ensure_dir(session_dir / "tiles"),
        "blankfield": ensure_dir(session_dir / "blankfield"),
        "anchors": ensure_dir(session_dir / "anchors"),
        "labels": ensure_dir(session_dir / "labels"),
        "logs": ensure_dir(session_dir / "logs"),
        "qc": ensure_dir(session_dir / "qc"),
    }

    config_snapshot = session_dir / "config_snapshot.toml"
    shutil.copy2(config_path, config_snapshot)

    manifest = {
        "created_utc": timestamp_utc(),
        "session_name": session_name,
        "sample_id": sample_id,
        "material": material,
        "substrate": substrate,
        "objective": objective,
        "operator": operator,
        "notes": notes,
        "paths": {name: str(path.resolve()) for name, path in subdirs.items()},
        "config_snapshot": str(config_snapshot.resolve()),
        "motion": {
            "port": config.motion.port,
            "travel_rate_um_s": config.motion.travel_rate_um_s,
            "bounds_um": {
                "min_x": config.motion.min_x_um,
                "min_y": config.motion.min_y_um,
                "max_x": config.motion.max_x_um,
                "max_y": config.motion.max_y_um,
            },
            "safety_margin_um": config.motion.safety_margin_um,
        },
        "camera": {
            "driver": config.camera.driver,
            "output_extension": config.camera.output_extension,
            "incoming_dir": config.camera.incoming_dir,
        },
        "scan": {
            "fov_width_um": config.scan.fov_width_um,
            "fov_height_um": config.scan.fov_height_um,
            "overlap_fraction": config.scan.overlap_fraction,
        },
    }

    manifest_path = session_dir / "session_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
