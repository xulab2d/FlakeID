from __future__ import annotations

import math

import cv2
import numpy as np

from flakefinder.config.models import AppConfig

from .base import Candidate


def _mask_compactness(mask: np.ndarray | None) -> float:
    if mask is None:
        return 0.0
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0.0
    contour = max(contours, key=cv2.contourArea)
    area = max(cv2.contourArea(contour), 1.0)
    perimeter = max(cv2.arcLength(contour, True), 1.0)
    return float((4.0 * np.pi * area) / (perimeter * perimeter))


def _edge_straightness(mask: np.ndarray | None) -> float:
    if mask is None:
        return 0.0
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return 0.0
    contour = max(contours, key=cv2.contourArea)
    approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
    return min(1.0, len(approx) / 8.0)


def _background_cleanliness(image: np.ndarray, bbox: tuple[int, int, int, int]) -> float:
    x, y, w, h = bbox
    pad = 10
    x0 = max(x - pad, 0)
    y0 = max(y - pad, 0)
    x1 = min(x + w + pad, image.shape[1])
    y1 = min(y + h + pad, image.shape[0])
    patch = image[y0:y1, x0:x1]
    if patch.size == 0:
        return 0.0
    return float(1.0 / (1.0 + np.std(patch.astype(np.float32))))


def rank_candidates(candidates: list[Candidate], image: np.ndarray, focus_score: float, config: AppConfig) -> list[tuple[Candidate, float]]:
    weights = config.ranking.weights
    ranked: list[tuple[Candidate, float]] = []
    centroids = np.array([candidate.centroid_xy for candidate in candidates], dtype=np.float32) if candidates else np.empty((0, 2))
    for idx, candidate in enumerate(candidates):
        distances = np.linalg.norm(centroids - centroids[idx], axis=1) if len(centroids) else np.array([0.0])
        distances = distances[distances > 0]
        isolation = float(1.0 if len(distances) == 0 else min(np.min(distances) / 200.0, 1.0))
        area = candidate.features.get("area", candidate.bbox[2] * candidate.bbox[3])
        compactness = candidate.features.get("compactness", _mask_compactness(candidate.mask))
        edge_straightness = _edge_straightness(candidate.mask)
        cleanliness = _background_cleanliness(image, candidate.bbox)
        layer_score = config.ranking.layer_preferences.get(str(candidate.predicted_thickness), 0.5)
        contrast_sanity = float(min(1.0, candidate.confidence + 0.1))
        score = (
            weights.get("confidence", 0.25) * candidate.confidence
            + weights.get("area", 0.15) * min(math.log1p(area) / 10.0, 1.0)
            + weights.get("isolation", 0.1) * isolation
            + weights.get("edge_straightness", 0.1) * edge_straightness
            + weights.get("compactness", 0.1) * compactness
            + weights.get("background_cleanliness", 0.1) * cleanliness
            + weights.get("focus_score", 0.1) * min(focus_score / 500.0, 1.0)
            + weights.get("layer_bin", 0.05) * layer_score
            + weights.get("contrast_sanity", 0.05) * contrast_sanity
        )
        candidate.features.update(
            {
                "isolation": isolation,
                "edge_straightness": edge_straightness,
                "compactness": compactness,
                "background_cleanliness": cleanliness,
                "focus_score": focus_score,
                "contrast_sanity": contrast_sanity,
            }
        )
        ranked.append((candidate, float(score)))
    return sorted(ranked, key=lambda item: item[1], reverse=True)
