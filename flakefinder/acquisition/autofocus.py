from __future__ import annotations

from flakefinder.config.models import AppConfig
from flakefinder.hardware.base import FocusInterface


def maybe_autofocus(focus: FocusInterface, config: AppConfig) -> float:
    if config.focus.mode == "none":
        return focus.get_position()
    return focus.autofocus()
