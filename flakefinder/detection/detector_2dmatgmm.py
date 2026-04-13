from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import cv2
import numpy as np

from flakefinder.config.models import AppConfig

from .base import Candidate, Detector

logger = logging.getLogger(__name__)


class Detector2DMatGMM(Detector):
    def __init__(self, config: AppConfig, workspace_root: str | Path | None = None):
        self.config = config
        self.workspace_root = Path(workspace_root or Path.cwd().parent)
        self._upstream = None
        self._model_version = "heuristic-bootstrap"
        self._init_upstream()

    @property
    def model_version(self) -> str:
        return self._model_version

    def _candidate_model_paths(self) -> list[Path]:
        paths: list[Path] = []
        if self.config.detector.model_path:
            paths.append(Path(self.config.detector.model_path))
        material = self.config.material.lower()
        if "graphene" in material:
            paths.extend(
                [
                    self.workspace_root / "2DMatGMM" / "GMMDetector" / "trained_parameters" / "Graphene_GMM.json",
                    self.workspace_root / "2DMatGMM-System" / "Parameters" / "GMM_Parameters" / "graphene_90nm.json",
                ]
            )
        elif "hbn" in material:
            paths.append(self.workspace_root / "2DMatGMM-System" / "Parameters" / "GMM_Parameters" / "hbn_90nm.json")
        return [path for path in paths if path.exists()]

    def _init_upstream(self) -> None:
        repo_root = self.workspace_root / "2DMatGMM"
        if not repo_root.exists():
            return
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        try:
            from GMMDetector import MaterialDetector
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to import 2DMatGMM, using heuristic fallback: %s", exc)
            return
        for model_path in self._candidate_model_paths():
            try:
                with model_path.open("r", encoding="utf-8") as handle:
                    contrast_dict = json.load(handle)
                self._upstream = MaterialDetector(
                    contrast_dict=contrast_dict,
                    size_threshold=self.config.detector.size_threshold,
                    standard_deviation_threshold=self.config.detector.std_threshold,
                    used_channels=self.config.detector.used_channels,
                    false_positive_detector_path=self.config.detector.false_positive_model,
                )
                self._model_version = f"2dmatgmm:{model_path.name}"
                logger.info("Using upstream 2DMatGMM model: %s", model_path)
                return
            except Exception as exc:  # pragma: no cover
                logger.warning("Could not initialize upstream detector from %s: %s", model_path, exc)

    def detect(self, image: np.ndarray) -> list[Candidate]:
        if self._upstream is not None:
            try:
                return self._detect_upstream(image)
            except Exception as exc:  # pragma: no cover
                logger.warning("Upstream 2DMatGMM inference failed, falling back to heuristic detector: %s", exc)
        return self._detect_heuristic(image)

    def _detect_upstream(self, image: np.ndarray) -> list[Candidate]:
        flakes = self._upstream(image)
        candidates: list[Candidate] = []
        for flake in flakes:
            confidence = float(max(0.0, min(1.0, 1.0 - getattr(flake, "false_positive_probability", 0.5))))
            mask = getattr(flake, "mask", None)
            if mask is None:
                continue
            x, y, w, h = cv2.boundingRect(mask.astype(np.uint8))
            area = float(np.sum(mask > 0))
            candidates.append(
                Candidate(
                    bbox=(int(x), int(y), int(w), int(h)),
                    centroid_xy=(float(flake.center[0]), float(flake.center[1])),
                    confidence=confidence,
                    predicted_material=self.config.material,
                    predicted_thickness=str(getattr(flake, "thickness", "unknown")),
                    features={"area": area},
                    mask=mask.astype(np.uint8),
                )
            )
        return candidates

    def _detect_heuristic(self, image: np.ndarray) -> list[Candidate]:
        preview = image if image.dtype == np.uint8 else cv2.convertScaleAbs(image, alpha=255.0 / max(float(image.max()), 1.0))
        if preview.ndim == 2:
            preview = cv2.cvtColor(preview, cv2.COLOR_GRAY2BGR)
        gray = cv2.cvtColor(preview, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        background = cv2.medianBlur(blurred, 31)
        contrast = cv2.absdiff(blurred, background)
        _, binary = cv2.threshold(contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates: list[Candidate] = []
        for contour in contours:
            area = float(cv2.contourArea(contour))
            if area < self.config.detector.size_threshold:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            mask = np.zeros(gray.shape, dtype=np.uint8)
            cv2.drawContours(mask, [contour], -1, 255, thickness=-1)
            centroid = (x + (w / 2.0), y + (h / 2.0))
            perimeter = max(cv2.arcLength(contour, True), 1.0)
            compactness = float((4.0 * np.pi * area) / (perimeter * perimeter))
            layer = "thin" if compactness > 0.5 else "thick"
            confidence = min(0.95, 0.3 + (area / (gray.shape[0] * gray.shape[1])) * 4.0 + compactness * 0.4)
            candidates.append(
                Candidate(
                    bbox=(x, y, w, h),
                    centroid_xy=centroid,
                    confidence=float(confidence),
                    predicted_material=self.config.material,
                    predicted_thickness=layer,
                    features={"area": area, "compactness": compactness},
                    mask=mask,
                )
            )
        return candidates
