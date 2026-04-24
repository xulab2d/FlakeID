from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import tomllib


@dataclass(slots=True)
class MotionConfig:
    driver: str = "grbl"
    port: str = "COM3"
    baud: int = 115200
    travel_rate_um_s: float = 2500.0
    settle_time_ms: int = 250
    startup_delay_ms: int = 500
    jog_feed_mm_min: float = 30.0
    x_max_rate_mm_min: float | None = None
    y_max_rate_mm_min: float | None = None
    x_accel_mm_s2: float | None = None
    y_accel_mm_s2: float | None = None
    min_x_um: float = 0.0
    min_y_um: float = 0.0
    max_x_um: float | None = None
    max_y_um: float | None = None
    safety_margin_um: float = 500.0


@dataclass(slots=True)
class CameraConfig:
    driver: str = "external_command"
    capture_command: str = ""
    output_extension: str = ".jpg"
    incoming_dir: str = ""
    watch_timeout_s: float = 30.0
    watch_stability_ms: int = 500
    watch_extensions: str = ".jpg,.jpeg,.png,.tif,.tiff"


@dataclass(slots=True)
class ScanConfig:
    fov_width_um: float = 260.0
    fov_height_um: float = 195.0
    overlap_fraction: float = 0.12
    origin_x_um: float = 0.0
    origin_y_um: float = 0.0
    photo_root_dir: str = "photos/scans"
    allow_out_of_bounds: bool = False
    roi_min_x_um: float | None = None
    roi_max_x_um: float | None = None
    roi_min_y_um: float | None = None
    roi_max_y_um: float | None = None


@dataclass(slots=True)
class DetectorConfig:
    min_area_px: int = 80
    max_area_px: int = 350000
    contrast_sigma: float = 2.8
    saturation_sigma: float = 2.1
    edge_sigma: float = 1.8
    border_crop_px: int = 8
    open_iterations: int = 1
    close_iterations: int = 2


@dataclass(slots=True)
class SubstratePreset:
    name: str
    material: str
    oxide_thickness_nm: float
    process: str
    recommended_clusters: int = 4
    notes: str = ""


@dataclass(slots=True)
class LabConfig:
    name: str = "2D Material Microscope"
    motion: MotionConfig = field(default_factory=MotionConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    scan: ScanConfig = field(default_factory=ScanConfig)
    detector: DetectorConfig = field(default_factory=DetectorConfig)
    substrates: dict[str, SubstratePreset] = field(default_factory=dict)


def _merge_dataclass(cls: type, raw: dict[str, Any]) -> Any:
    fields = {field.name for field in cls.__dataclass_fields__.values()}
    selected = {key: value for key, value in raw.items() if key in fields}
    return cls(**selected)


def load_lab_config(path: str | Path) -> LabConfig:
    config_path = Path(path)
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)

    motion = _merge_dataclass(MotionConfig, raw.get("motion", {}))
    camera = _merge_dataclass(CameraConfig, raw.get("camera", {}))
    scan = _merge_dataclass(ScanConfig, raw.get("scan", {}))
    detector = _merge_dataclass(DetectorConfig, raw.get("detector", {}))

    substrates: dict[str, SubstratePreset] = {}
    for name, payload in raw.get("substrates", {}).items():
        substrates[name] = SubstratePreset(name=name, **payload)

    lab_name = raw.get("lab", {}).get("name", "2D Material Microscope")
    return LabConfig(
        name=lab_name,
        motion=motion,
        camera=camera,
        scan=scan,
        detector=detector,
        substrates=substrates,
    )
