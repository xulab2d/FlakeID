from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class Camera(ABC):
    @abstractmethod
    def capture(self, output_path: str | Path) -> Path:
        raise NotImplementedError

