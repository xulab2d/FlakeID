from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(slots=True)
class Candidate:
    bbox: tuple[int, int, int, int]
    centroid_xy: tuple[float, float]
    confidence: float
    predicted_material: str
    predicted_thickness: str | None
    features: dict[str, float] = field(default_factory=dict)
    mask: np.ndarray | None = None


class Detector(ABC):
    @abstractmethod
    def detect(self, image: np.ndarray) -> list[Candidate]:
        raise NotImplementedError

    @property
    @abstractmethod
    def model_version(self) -> str:
        raise NotImplementedError


class FalsePositiveFilter(ABC):
    @abstractmethod
    def keep(self, candidate: Candidate) -> bool:
        raise NotImplementedError
