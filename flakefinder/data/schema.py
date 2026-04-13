from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ScanRecord:
    scan_id: str
    config_key: str
    mode: str
    input_path: str
    output_dir: str
    model_version: str


@dataclass(slots=True)
class TileRecord:
    tile_id: str
    scan_id: str
    x_mm: float
    y_mm: float
    z_um: float
    timestamp_utc: str
    objective: str
    exposure_ms: float
    gain: float
    illumination_json: str
    config_key: str
    raw_path: str
    preview_path: str
    focus_score: float
    qc_passed: bool


@dataclass(slots=True)
class CandidateRecord:
    candidate_id: str
    tile_id: str
    bbox_json: str
    centroid_json: str
    predicted_material: str
    predicted_thickness: str | None
    confidence: float
    ranking_score: float
    features_json: str
    mask_path: str | None
    thumbnail_path: str | None
    review_state: str
    config_version: str
    model_version: str
