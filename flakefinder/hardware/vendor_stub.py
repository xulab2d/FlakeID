from __future__ import annotations

from .base import CameraInterface, FocusInterface, HardwareBundle, IlluminationInterface, StageInterface


class _VendorNotImplemented(CameraInterface, StageInterface, FocusInterface, IlluminationInterface):
    def snap_image(self):  # type: ignore[override]
        raise NotImplementedError("TODO: implement direct vendor camera acquisition.")

    def set_exposure(self, exposure_ms: float) -> None:
        raise NotImplementedError("TODO: implement direct vendor camera exposure control.")

    def set_gain(self, gain: float) -> None:
        raise NotImplementedError("TODO: implement direct vendor camera gain control.")

    def move_absolute(self, x_mm: float, y_mm: float) -> None:
        raise NotImplementedError("TODO: implement direct vendor stage absolute motion.")

    def move_relative(self, dx_mm: float, dy_mm: float) -> None:
        raise NotImplementedError("TODO: implement direct vendor stage relative motion.")

    def get_position(self):  # type: ignore[override]
        raise NotImplementedError("TODO: implement direct vendor stage/focus readback.")

    def move_to(self, z_um: float) -> None:
        raise NotImplementedError("TODO: implement direct vendor focus control.")

    def autofocus(self) -> float:
        raise NotImplementedError("TODO: implement vendor autofocus hook.")

    def set_illumination(self, settings):
        raise NotImplementedError("TODO: implement direct vendor illumination control.")

    def get_illumination(self):
        raise NotImplementedError("TODO: implement direct vendor illumination readback.")


class VendorSDKStub(HardwareBundle):
    def __init__(self) -> None:
        device = _VendorNotImplemented()
        super().__init__(camera=device, stage=device, focus=device, illumination=device)
