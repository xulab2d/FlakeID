from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class StagePosition:
    x_um: float
    y_um: float
    z_um: float | None = None


@dataclass(slots=True)
class ScanTile:
    index: int
    row: int
    column: int
    position: StagePosition
    width_um: float
    height_um: float
    overlap_fraction: float
    image_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["position"] = asdict(self.position)
        return data


@dataclass(slots=True)
class FlakeCandidate:
    tile_index: int
    bbox_xywh: tuple[int, int, int, int]
    area_px: int
    score: float
    label: str = "candidate"
    cluster_id: int | None = None
    features: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tile_index": self.tile_index,
            "bbox_xywh": list(self.bbox_xywh),
            "area_px": self.area_px,
            "score": self.score,
            "label": self.label,
            "cluster_id": self.cluster_id,
            "features": self.features,
        }


@dataclass(slots=True)
class DetectionResult:
    image_path: str
    width_px: int
    height_px: int
    candidates: list[FlakeCandidate]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "image_path": self.image_path,
            "width_px": self.width_px,
            "height_px": self.height_px,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "metadata": self.metadata,
        }

