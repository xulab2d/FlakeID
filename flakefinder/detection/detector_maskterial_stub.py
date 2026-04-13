from __future__ import annotations

from .base import Candidate, Detector


class MaskTerialDetectorStub(Detector):
    @property
    def model_version(self) -> str:
        return "maskterial-stub"

    def detect(self, image) -> list[Candidate]:
        # TODO: attach MaskTerial segmentation inference here without changing pipeline call sites.
        return []
