from __future__ import annotations

from .base import Candidate, FalsePositiveFilter


class ThresholdFalsePositiveFilter(FalsePositiveFilter):
    def __init__(self, confidence_threshold: float):
        self.confidence_threshold = confidence_threshold

    def keep(self, candidate: Candidate) -> bool:
        return candidate.confidence >= self.confidence_threshold
