from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..config import DetectorConfig
from ..models import DetectionResult, FlakeCandidate
from ..processing.features import component_feature_vector
from ..processing.preprocess import estimate_background, load_image, white_balance_from_border
from ..utils import rgb_to_hsv, robust_sigma
from .components import binary_close, binary_open, connected_components


@dataclass(slots=True)
class ClassicalFlakeDetector:
    config: DetectorConfig

    def detect(self, image: np.ndarray, image_path: str = "", tile_index: int = 0) -> DetectionResult:
        balanced = white_balance_from_border(image)
        background = estimate_background(balanced)
        difference = balanced - background
        hsv = rgb_to_hsv(balanced)
        luminance = np.mean(balanced, axis=2)
        gradient = np.sqrt(np.square(np.diff(luminance, axis=0, append=luminance[-1:, :])) + np.square(np.diff(luminance, axis=1, append=luminance[:, -1:])))

        contrast_strength = np.linalg.norm(difference, axis=2)
        saturation_deviation = np.abs(hsv[..., 1] - np.median(hsv[..., 1]))
        luminance_deviation = np.abs(luminance - np.median(luminance))

        contrast_threshold = self.config.contrast_sigma * robust_sigma(contrast_strength)
        saturation_threshold = self.config.saturation_sigma * robust_sigma(saturation_deviation)
        edge_threshold = self.config.edge_sigma * robust_sigma(gradient)

        mask = (
            (contrast_strength > contrast_threshold)
            | ((saturation_deviation > saturation_threshold) & (luminance_deviation > 0.5 * contrast_threshold))
            | ((gradient > edge_threshold) & (luminance_deviation > 0.5 * robust_sigma(luminance_deviation)))
        )

        border = self.config.border_crop_px
        if border > 0:
            mask[:border, :] = False
            mask[-border:, :] = False
            mask[:, :border] = False
            mask[:, -border:] = False

        mask = binary_open(mask, iterations=self.config.open_iterations)
        mask = binary_close(mask, iterations=self.config.close_iterations)

        candidates: list[FlakeCandidate] = []
        for component in connected_components(mask):
            area = int(component.sum())
            if area < self.config.min_area_px or area > self.config.max_area_px:
                continue

            ys, xs = np.where(component)
            x0 = int(xs.min())
            x1 = int(xs.max()) + 1
            y0 = int(ys.min())
            y1 = int(ys.max()) + 1
            width = x1 - x0
            height = y1 - y0

            mean_contrast = float(np.mean(contrast_strength[component]))
            std_inside = float(np.std(luminance[component]))
            fill_ratio = area / max(width * height, 1)
            edge_strength = float(np.mean(gradient[component]))
            score = (
                0.45 * min(mean_contrast / max(contrast_threshold, 1e-6), 3.0)
                + 0.25 * min(edge_strength / max(edge_threshold, 1e-6), 3.0)
                + 0.20 * min(fill_ratio * 2.0, 1.0)
                - 0.10 * min(std_inside / max(robust_sigma(luminance), 1e-6), 3.0)
            )
            label = "likely_flake" if score >= 1.2 else "possible_flake"
            features = component_feature_vector(balanced, component, score)
            candidates.append(
                FlakeCandidate(
                    tile_index=tile_index,
                    bbox_xywh=(x0, y0, width, height),
                    area_px=area,
                    score=float(score),
                    label=label,
                    features=features,
                )
            )

        candidates.sort(key=lambda candidate: candidate.score, reverse=True)
        return DetectionResult(
            image_path=image_path,
            width_px=image.shape[1],
            height_px=image.shape[0],
            candidates=candidates,
            metadata={
                "contrast_threshold": float(contrast_threshold),
                "saturation_threshold": float(saturation_threshold),
                "edge_threshold": float(edge_threshold),
            },
        )

    def detect_path(self, image_path: str | Path, tile_index: int = 0) -> DetectionResult:
        image = load_image(image_path)
        return self.detect(image=image, image_path=str(image_path), tile_index=tile_index)

