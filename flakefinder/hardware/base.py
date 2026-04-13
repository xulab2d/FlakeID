from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


class CameraInterface(ABC):
    @abstractmethod
    def snap_image(self) -> np.ndarray:
        raise NotImplementedError

    @abstractmethod
    def set_exposure(self, exposure_ms: float) -> None:
        raise NotImplementedError

    @abstractmethod
    def set_gain(self, gain: float) -> None:
        raise NotImplementedError


class StageInterface(ABC):
    @abstractmethod
    def move_absolute(self, x_mm: float, y_mm: float) -> None:
        raise NotImplementedError

    @abstractmethod
    def move_relative(self, dx_mm: float, dy_mm: float) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_position(self) -> tuple[float, float]:
        raise NotImplementedError


class FocusInterface(ABC):
    @abstractmethod
    def move_to(self, z_um: float) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_position(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def autofocus(self) -> float:
        raise NotImplementedError


class IlluminationInterface(ABC):
    @abstractmethod
    def set_illumination(self, settings: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_illumination(self) -> dict[str, Any]:
        raise NotImplementedError


@dataclass(slots=True)
class HardwareBundle:
    camera: CameraInterface
    stage: StageInterface
    focus: FocusInterface
    illumination: IlluminationInterface
    source_path: Path | None = None
