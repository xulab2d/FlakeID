from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from flakefinder.imaging.raw_io import load_image

from .base import CameraInterface, FocusInterface, HardwareBundle, IlluminationInterface, StageInterface


@dataclass
class _MockState:
    image_paths: list[Path]
    cursor: int = 0
    x_mm: float = 0.0
    y_mm: float = 0.0
    z_um: float = 0.0
    exposure_ms: float = 10.0
    gain: float = 0.0
    illumination: dict[str, float] = field(default_factory=lambda: {"brightness": 1.0})


class _MockCamera(CameraInterface):
    def __init__(self, state: _MockState):
        self.state = state

    def snap_image(self) -> np.ndarray:
        if not self.state.image_paths:
            return np.zeros((768, 1024, 3), dtype=np.uint16)
        image = load_image(self.state.image_paths[self.state.cursor % len(self.state.image_paths)])
        self.state.cursor += 1
        return image

    def set_exposure(self, exposure_ms: float) -> None:
        self.state.exposure_ms = exposure_ms

    def set_gain(self, gain: float) -> None:
        self.state.gain = gain


class _MockStage(StageInterface):
    def __init__(self, state: _MockState):
        self.state = state

    def move_absolute(self, x_mm: float, y_mm: float) -> None:
        self.state.x_mm = x_mm
        self.state.y_mm = y_mm

    def move_relative(self, dx_mm: float, dy_mm: float) -> None:
        self.state.x_mm += dx_mm
        self.state.y_mm += dy_mm

    def get_position(self) -> tuple[float, float]:
        return self.state.x_mm, self.state.y_mm


class _MockFocus(FocusInterface):
    def __init__(self, state: _MockState):
        self.state = state

    def move_to(self, z_um: float) -> None:
        self.state.z_um = z_um

    def get_position(self) -> float:
        return self.state.z_um

    def autofocus(self) -> float:
        return self.state.z_um


class _MockIllumination(IlluminationInterface):
    def __init__(self, state: _MockState):
        self.state = state

    def set_illumination(self, settings: dict[str, float]) -> None:
        self.state.illumination = dict(settings)

    def get_illumination(self) -> dict[str, float]:
        return dict(self.state.illumination)


class MockHardware(HardwareBundle):
    def __init__(self, input_dir: str | Path):
        input_path = Path(input_dir)
        image_paths = sorted(
            path
            for path in input_path.iterdir()
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".npy"}
        )
        state = _MockState(image_paths=image_paths)
        super().__init__(
            camera=_MockCamera(state),
            stage=_MockStage(state),
            focus=_MockFocus(state),
            illumination=_MockIllumination(state),
            source_path=input_path,
        )
