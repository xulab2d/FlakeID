from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ROI:
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float


@dataclass(slots=True)
class CameraDefaults:
    exposure_ms: float
    gain: float
    illumination: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FocusStrategy:
    mode: str = "none"
    step_um: float = 1.0
    sweep_um: float = 10.0


@dataclass(slots=True)
class PreprocessingConfig:
    demosaic: bool = False
    linearize: bool = False
    darkframe_subtraction: bool = False
    flatfield_correction: bool = False
    normalize_background: bool = True
    clip_percentile_low: float = 0.5
    clip_percentile_high: float = 99.5
    darkframe_path: str | None = None
    flatfield_path: str | None = None


@dataclass(slots=True)
class DetectorConfig:
    name: str = "2dmatgmm"
    model_path: str | None = None
    false_positive_model: str | None = None
    size_threshold: int = 300
    std_threshold: float = 5.0
    confidence_threshold: float = 0.25
    used_channels: str = "BGR"
    fallback_to_heuristic: bool = True


@dataclass(slots=True)
class RankingConfig:
    weights: dict[str, float] = field(default_factory=dict)
    layer_preferences: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class OutputConfig:
    run_root: str = "runs"
    save_previews: bool = True
    save_masks: bool = True
    sqlite_path: str = "storage/flakefinder.db"


@dataclass(slots=True)
class HardwareConfig:
    backend: str = "mock"
    objective: str = "20x"
    pixel_size_um: float = 0.5
    frame_width_px: int = 1024
    frame_height_px: int = 768
    overlap: float = 0.1
    roi: ROI = field(default_factory=lambda: ROI(0.0, 0.0, 5.0, 5.0))


@dataclass(slots=True)
class AppConfig:
    config_key: str
    material: str
    substrate: str
    oxide_thickness_nm: int
    objective_magnification: int
    config_version: str
    hardware: HardwareConfig
    camera: CameraDefaults
    focus: FocusStrategy
    preprocessing: PreprocessingConfig
    detector: DetectorConfig
    ranking: RankingConfig
    outputs: OutputConfig

    def resolve_path(self, value: str | None, base_dir: Path) -> Path | None:
        if not value:
            return None
        path = Path(value)
        return path if path.is_absolute() else base_dir / path
