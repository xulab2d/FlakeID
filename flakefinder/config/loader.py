from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import (
    AppConfig,
    CameraDefaults,
    DetectorConfig,
    FocusStrategy,
    HardwareConfig,
    OutputConfig,
    PreprocessingConfig,
    ROI,
    RankingConfig,
)


def _section(data: dict[str, Any], key: str) -> dict[str, Any]:
    return dict(data.get(key, {}))


def load_app_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    hardware_section = _section(raw, "hardware")
    roi = ROI(**hardware_section.pop("roi"))
    hardware = HardwareConfig(roi=roi, **hardware_section)

    return AppConfig(
        config_key=raw["config_key"],
        material=raw["material"],
        substrate=raw["substrate"],
        oxide_thickness_nm=int(raw["oxide_thickness_nm"]),
        objective_magnification=int(raw["objective_magnification"]),
        config_version=str(raw.get("config_version", "0.1.0")),
        hardware=hardware,
        camera=CameraDefaults(**_section(raw, "camera")),
        focus=FocusStrategy(**_section(raw, "focus")),
        preprocessing=PreprocessingConfig(**_section(raw, "preprocessing")),
        detector=DetectorConfig(**_section(raw, "detector")),
        ranking=RankingConfig(**_section(raw, "ranking")),
        outputs=OutputConfig(**_section(raw, "outputs")),
    )
