from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RevisitRequest:
    candidate_id: str
    x_mm: float
    y_mm: float
    target_objective: str


def build_revisit_request(candidate_id: str, x_mm: float, y_mm: float, target_objective: str = "50x") -> RevisitRequest:
    return RevisitRequest(candidate_id=candidate_id, x_mm=x_mm, y_mm=y_mm, target_objective=target_objective)
