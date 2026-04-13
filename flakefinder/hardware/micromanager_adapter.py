from __future__ import annotations

from typing import Any

import numpy as np

from .base import CameraInterface, FocusInterface, HardwareBundle, IlluminationInterface, StageInterface


class _MMCamera(CameraInterface):
    def __init__(self, core: Any):
        self.core = core

    def snap_image(self) -> np.ndarray:
        self.core.snap_image()
        image = self.core.get_image()
        return np.asarray(image)

    def set_exposure(self, exposure_ms: float) -> None:
        self.core.set_exposure(exposure_ms)

    def set_gain(self, gain: float) -> None:
        # TODO: map the actual camera gain property name once the hardware stack is known.
        self.core.set_property(self.core.get_camera_device(), "Gain", gain)


class _MMStage(StageInterface):
    def __init__(self, core: Any):
        self.core = core

    def move_absolute(self, x_mm: float, y_mm: float) -> None:
        # TODO: validate whether the stage reports microns or millimeters for the final device.
        self.core.set_xy_position(x_mm * 1000.0, y_mm * 1000.0)
        self.core.wait_for_system()

    def move_relative(self, dx_mm: float, dy_mm: float) -> None:
        x_um, y_um = self.core.get_xy_stage_position()
        self.move_absolute((x_um / 1000.0) + dx_mm, (y_um / 1000.0) + dy_mm)

    def get_position(self) -> tuple[float, float]:
        x_um, y_um = self.core.get_xy_stage_position()
        return x_um / 1000.0, y_um / 1000.0


class _MMFocus(FocusInterface):
    def __init__(self, core: Any):
        self.core = core

    def move_to(self, z_um: float) -> None:
        self.core.set_position(z_um)
        self.core.wait_for_system()

    def get_position(self) -> float:
        return float(self.core.get_position())

    def autofocus(self) -> float:
        # TODO: bind the final autofocus device or plugin if available in the microscope stack.
        return self.get_position()


class _MMIllumination(IlluminationInterface):
    def __init__(self, core: Any):
        self.core = core
        self._last: dict[str, Any] = {}

    def set_illumination(self, settings: dict[str, Any]) -> None:
        self._last = dict(settings)
        # TODO: map illumination channel/property names for the final microscope.
        for key, value in settings.items():
            self.core.set_property(self.core.get_shutter_device(), key, value)

    def get_illumination(self) -> dict[str, Any]:
        return dict(self._last)


class MicroManagerHardware(HardwareBundle):
    def __init__(self) -> None:
        try:
            from pycromanager import Core
        except ImportError as exc:
            raise RuntimeError("pycro-manager is not installed. Use the hardware extra.") from exc

        core = Core()
        super().__init__(
            camera=_MMCamera(core),
            stage=_MMStage(core),
            focus=_MMFocus(core),
            illumination=_MMIllumination(core),
        )
