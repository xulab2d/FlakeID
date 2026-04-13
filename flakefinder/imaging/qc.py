from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .focus_metrics import focus_score


@dataclass(slots=True)
class TileQC:
    passed: bool
    focus_score: float
    saturation_fraction: float


def evaluate_tile_qc(image: np.ndarray, min_focus: float = 10.0, max_saturation_fraction: float = 0.05) -> TileQC:
    score = focus_score(image)
    image_max = float(np.max(image)) if image.size else 1.0
    saturation_fraction = float((image >= image_max).mean())
    passed = score >= min_focus and saturation_fraction <= max_saturation_fraction
    return TileQC(passed=passed, focus_score=score, saturation_fraction=saturation_fraction)
