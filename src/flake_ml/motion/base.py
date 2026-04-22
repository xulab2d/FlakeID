from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import StagePosition


class MotionController(ABC):
    @abstractmethod
    def home(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def move_abs(self, x_um: float, y_um: float) -> None:
        raise NotImplementedError

    @abstractmethod
    def wait_for_idle(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def current_position(self) -> StagePosition:
        raise NotImplementedError


class DryRunMotionController(MotionController):
    def __init__(self) -> None:
        self._position = StagePosition(0.0, 0.0)

    def home(self) -> None:
        self._position = StagePosition(0.0, 0.0)

    def move_abs(self, x_um: float, y_um: float) -> None:
        self._position = StagePosition(float(x_um), float(y_um))

    def wait_for_idle(self) -> None:
        return None

    def current_position(self) -> StagePosition:
        return self._position

