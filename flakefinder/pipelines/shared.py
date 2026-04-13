from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import cv2

from flakefinder.config.models import AppConfig
from flakefinder.data.exporters import export_candidates
from flakefinder.data.schema import CandidateRecord, ScanRecord, TileRecord
from flakefinder.data.storage import Storage
from flakefinder.detection.detector_2dmatgmm import Detector2DMatGMM
from flakefinder.detection.false_positive_filter import ThresholdFalsePositiveFilter
from flakefinder.detection.ranking import rank_candidates
from flakefinder.imaging.normalize import preprocess_image
from flakefinder.imaging.qc import evaluate_tile_qc
from flakefinder.imaging.raw_io import load_image, save_image
from flakefinder.utils.image_ops import crop_thumbnail
from flakefinder.utils.paths import prepare_run_dirs

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]


def run_pipeline(
    config: AppConfig,
    tile_paths: list[Path],
    input_path: Path,
    output_dir: Path,
    mode: str,
    planned_tiles: list[object] | None = None,
) -> dict[str, object]:
    run_dirs = prepare_run_dirs(output_dir)
    storage = Storage(run_dirs.database_path)
    detector = Detector2DMatGMM(config=config, workspace_root=WORKSPACE_ROOT)
    fp_filter = ThresholdFalsePositiveFilter(config.detector.confidence_threshold)
    scan_id = uuid.uuid4().hex
    storage.insert_scan(
        ScanRecord(
            scan_id=scan_id,
            config_key=config.config_key,
            mode=mode,
            input_path=str(input_path),
            output_dir=str(output_dir),
            model_version=detector.model_version,
        )
    )
    total_candidates = 0
    for index, tile_path in enumerate(tile_paths):
        raw = load_image(tile_path)
        _, preview = preprocess_image(raw, config)
        qc = evaluate_tile_qc(preview)
        tile_id = uuid.uuid4().hex
        preview_path = run_dirs.previews / f"{tile_id}.png"
        raw_copy_path = run_dirs.raw / tile_path.name
        save_image(preview_path, preview)
        save_image(raw_copy_path, raw)
        x_mm = planned_tiles[index].x_mm if planned_tiles and index < len(planned_tiles) else 0.0
        y_mm = planned_tiles[index].y_mm if planned_tiles and index < len(planned_tiles) else 0.0
        storage.insert_tile(
            TileRecord(
                tile_id=tile_id,
                scan_id=scan_id,
                x_mm=x_mm,
                y_mm=y_mm,
                z_um=0.0,
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                objective=f"{config.objective_magnification}x",
                exposure_ms=config.camera.exposure_ms,
                gain=config.camera.gain,
                illumination_json=json.dumps(config.camera.illumination),
                config_key=config.config_key,
                raw_path=str(raw_copy_path),
                preview_path=str(preview_path),
                focus_score=qc.focus_score,
                qc_passed=qc.passed,
            )
        )
        ranked = rank_candidates(
            [candidate for candidate in detector.detect(preview) if fp_filter.keep(candidate)],
            preview,
            qc.focus_score,
            config,
        )
        for rank_idx, (candidate, score) in enumerate(ranked):
            candidate_id = uuid.uuid4().hex
            mask_path = None
            if candidate.mask is not None and config.outputs.save_masks:
                mask_path = run_dirs.masks / f"{candidate_id}.png"
                save_image(mask_path, candidate.mask)
            thumb = crop_thumbnail(preview, candidate.bbox)
            thumbnail_path = run_dirs.thumbnails / f"{candidate_id}.png"
            save_image(thumbnail_path, thumb)
            candidate.features["rank_order"] = float(rank_idx)
            storage.insert_candidate(
                CandidateRecord(
                    candidate_id=candidate_id,
                    tile_id=tile_id,
                    bbox_json=json.dumps(candidate.bbox),
                    centroid_json=json.dumps(candidate.centroid_xy),
                    predicted_material=candidate.predicted_material,
                    predicted_thickness=candidate.predicted_thickness,
                    confidence=candidate.confidence,
                    ranking_score=score,
                    features_json=json.dumps(candidate.features),
                    mask_path=str(mask_path) if mask_path else None,
                    thumbnail_path=str(thumbnail_path),
                    review_state="unreviewed",
                    config_version=config.config_version,
                    model_version=detector.model_version,
                )
            )
            total_candidates += 1
    export_candidates(storage, run_dirs.exports, "csv")
    export_candidates(storage, run_dirs.exports, "parquet")
    storage.close()
    return {"scan_id": scan_id, "tiles": len(tile_paths), "candidates": total_candidates, "output_dir": str(output_dir)}
