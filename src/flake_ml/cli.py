from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from typing import Iterable

import numpy as np
from PIL import Image, ImageDraw

from .camera_probe import probe_camera_environment
from .annotation.coco import export_catalog_to_coco
from .catalog import CatalogStore
from .config import load_lab_config
from .detection.classical import ClassicalFlakeDetector
from .learning.gmm import GaussianMixtureModel
from .models import ScanTile, StagePosition
from .processing.preprocess import build_flat_field, load_image
from .registration import estimate_overlap_shift_from_paths
from .scanning.planner import build_serpentine_plan
from .scanning.runtime import run_capture_scan
from .session import initialize_session
from .utils import normalize_vector


def _write_json(path: str | Path, payload: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _validate_tiles_within_bounds(tiles: list[ScanTile], args: argparse.Namespace, config) -> None:
    max_x_um = config.motion.max_x_um
    max_y_um = config.motion.max_y_um
    min_x_um = config.motion.min_x_um
    min_y_um = config.motion.min_y_um
    margin_um = config.motion.safety_margin_um

    if max_x_um is None or max_y_um is None:
        return

    planned_max_x = max(tile.position.x_um for tile in tiles)
    planned_max_y = max(tile.position.y_um for tile in tiles)
    planned_min_x = min(tile.position.x_um for tile in tiles)
    planned_min_y = min(tile.position.y_um for tile in tiles)

    safe_max_x = max_x_um - margin_um
    safe_max_y = max_y_um - margin_um
    safe_min_x = min_x_um
    safe_min_y = min_y_um

    failures: list[str] = []
    if planned_min_x < safe_min_x:
        failures.append(f"planned minimum X {planned_min_x:.1f} um is below safe minimum {safe_min_x:.1f} um")
    if planned_min_y < safe_min_y:
        failures.append(f"planned minimum Y {planned_min_y:.1f} um is below safe minimum {safe_min_y:.1f} um")
    if planned_max_x > safe_max_x:
        failures.append(f"planned maximum X {planned_max_x:.1f} um exceeds safe maximum {safe_max_x:.1f} um")
    if planned_max_y > safe_max_y:
        failures.append(f"planned maximum Y {planned_max_y:.1f} um exceeds safe maximum {safe_max_y:.1f} um")

    if failures:
        joined = "; ".join(failures)
        raise ValueError(
            "Scan plan falls outside configured safe motion bounds. "
            "Update motion.max_x_um / motion.max_y_um after bound finding, or reduce the scan region. "
            f"Details: {joined}"
        )


def _overlay_candidates(image_path: str | Path, candidates: Iterable, output_path: str | Path) -> None:
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    for candidate in candidates:
        x, y, w, h = candidate.bbox_xywh
        color = "red" if candidate.label == "likely_flake" else "yellow"
        draw.rectangle([x, y, x + w, y + h], outline=color, width=3)
        draw.text((x, max(0, y - 14)), f"{candidate.score:.2f}", fill=color)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def command_scan_plan(args: argparse.Namespace) -> None:
    config = load_lab_config(args.config)
    tiles = build_serpentine_plan(
        width_um=args.width_mm * 1000.0,
        height_um=args.height_mm * 1000.0,
        fov_width_um=config.scan.fov_width_um,
        fov_height_um=config.scan.fov_height_um,
        overlap_fraction=config.scan.overlap_fraction,
        origin_x_um=config.scan.origin_x_um,
        origin_y_um=config.scan.origin_y_um,
    )
    _validate_tiles_within_bounds(tiles, args, config)
    payload = {
        "count": len(tiles),
        "tiles": [tile.to_dict() for tile in tiles],
    }
    _write_json(args.output, payload)
    print(f"Wrote {len(tiles)} tiles to {args.output}")


def command_detect_image(args: argparse.Namespace) -> None:
    config = load_lab_config(args.config)
    detector = ClassicalFlakeDetector(config.detector)
    result = detector.detect_path(args.image_path)
    _write_json(args.output_json, result.to_dict())
    if args.overlay:
        _overlay_candidates(args.image_path, result.candidates, args.overlay)
    print(f"Detected {len(result.candidates)} candidates in {args.image_path}")


def command_build_flatfield(args: argparse.Namespace) -> None:
    images = [load_image(path) for path in args.images]
    flat_field = build_flat_field(images)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    np.save(output, flat_field)
    print(f"Saved flat-field array to {output}")


def _tile_from_index(index: int, total: int, width_um: float, height_um: float) -> ScanTile:
    columns = max(1, int(np.ceil(np.sqrt(total))))
    row = index // columns
    column = index % columns
    return ScanTile(
        index=index,
        row=row,
        column=column,
        position=StagePosition(x_um=column * width_um, y_um=row * height_um),
        width_um=width_um,
        height_um=height_um,
        overlap_fraction=0.0,
    )


def command_replay_folder(args: argparse.Namespace) -> None:
    config = load_lab_config(args.config)
    detector = ClassicalFlakeDetector(config.detector)
    store = CatalogStore(args.catalog)
    store.init()
    scan_id = store.create_scan(sample_id=args.sample_id, material=args.material, config_path=args.config)

    image_paths = sorted(
        path for path in Path(args.image_dir).iterdir() if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    )
    if not image_paths:
        raise FileNotFoundError(f"No images found in {args.image_dir}")

    feature_rows: list[np.ndarray] = []
    candidate_ids: list[int] = []
    for index, image_path in enumerate(image_paths):
        tile = _tile_from_index(index, len(image_paths), config.scan.fov_width_um, config.scan.fov_height_um)
        tile.image_path = str(image_path)
        store.record_tile(scan_id, tile)
        result = detector.detect_path(image_path, tile_index=index)
        store.record_candidates(scan_id, str(image_path), result.candidates)

    rows = store.fetch_candidate_rows(scan_id)
    for row in rows:
        feature_dict = json.loads(row["features_json"])
        feature_rows.append(
            np.array(
                [
                    feature_dict["mean_r"],
                    feature_dict["mean_g"],
                    feature_dict["mean_b"],
                    feature_dict["mean_s"],
                    feature_dict["mean_v"],
                    feature_dict["std_luma"],
                    feature_dict["score"],
                ],
                dtype=np.float32,
            )
        )
        candidate_ids.append(int(row["id"]))

    if feature_rows and len(feature_rows) >= args.clusters:
        features = normalize_vector(np.stack(feature_rows, axis=0))
        model = GaussianMixtureModel(n_components=args.clusters, max_iter=150).fit(features)
        assignments = model.predict(features)
        store.update_clusters({candidate_id: int(cluster_id) for candidate_id, cluster_id in zip(candidate_ids, assignments)})

    print(f"Replay complete. Scan {scan_id} recorded with {len(rows)} candidates.")


def command_export_coco(args: argparse.Namespace) -> None:
    payload = export_catalog_to_coco(args.catalog, args.output, score_threshold=args.score_threshold)
    print(
        f"Exported {len(payload['annotations'])} annotations across {len(payload['images'])} images to {args.output}"
    )


def command_camera_probe(args: argparse.Namespace) -> None:
    payload = probe_camera_environment()
    if args.output:
        _write_json(args.output, payload)
    print(json.dumps(payload, indent=2))


def command_init_session(args: argparse.Namespace) -> None:
    config = load_lab_config(args.config)
    manifest = initialize_session(
        output_root=args.output_root,
        config_path=args.config,
        config=config,
        sample_id=args.sample_id,
        material=args.material,
        substrate=args.substrate,
        objective=args.objective,
        operator=args.operator,
        notes=args.notes,
    )
    print(json.dumps(manifest, indent=2))


def command_estimate_shift(args: argparse.Namespace) -> None:
    estimate = estimate_overlap_shift_from_paths(
        args.reference_image,
        args.moving_image,
        axis=args.axis,
        overlap_fraction=args.overlap_fraction,
    )
    payload = estimate.to_dict()
    if args.output_json:
        _write_json(args.output_json, payload)
    print(json.dumps(payload, indent=2))


def command_run_scan(args: argparse.Namespace) -> None:
    config = load_lab_config(args.config)
    roi_min_x_um = args.roi_min_x_um if args.roi_min_x_um is not None else config.scan.roi_min_x_um
    roi_max_x_um = args.roi_max_x_um if args.roi_max_x_um is not None else config.scan.roi_max_x_um
    roi_min_y_um = args.roi_min_y_um if args.roi_min_y_um is not None else config.scan.roi_min_y_um
    roi_max_y_um = args.roi_max_y_um if args.roi_max_y_um is not None else config.scan.roi_max_y_um

    missing = [
        name
        for name, value in {
            "roi_min_x_um": roi_min_x_um,
            "roi_max_x_um": roi_max_x_um,
            "roi_min_y_um": roi_min_y_um,
            "roi_max_y_um": roi_max_y_um,
        }.items()
        if value is None
    ]
    if missing:
        raise ValueError(f"Scan ROI is incomplete. Provide {', '.join(missing)} or save the scan ROI in the config.")

    output_root = args.output_root or config.scan.photo_root_dir
    summary = run_capture_scan(
        config_path=args.config,
        config=config,
        sample_id=args.sample_id,
        material=args.material,
        substrate=args.substrate,
        objective=args.objective,
        operator=args.operator,
        notes=args.notes,
        roi_min_x_um=float(roi_min_x_um),
        roi_max_x_um=float(roi_max_x_um),
        roi_min_y_um=float(roi_min_y_um),
        roi_max_y_um=float(roi_max_y_um),
        output_root=output_root,
        log=lambda message: print(message, flush=True),
    )
    print(json.dumps(summary, indent=2))


def command_stage_ui(args: argparse.Namespace) -> None:
    launcher = Path(__file__).resolve().parents[2] / "scripts" / "stage_calibration_ui.ps1"
    subprocess.Popen(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(launcher),
            "-Config",
            str(Path(args.config).resolve()),
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Automated flake discovery starter CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_plan = subparsers.add_parser("scan-plan", help="Generate a serpentine XY scan plan.")
    scan_plan.add_argument("--config", required=True)
    scan_plan.add_argument("--width-mm", type=float, required=True)
    scan_plan.add_argument("--height-mm", type=float, required=True)
    scan_plan.add_argument("--output", required=True)
    scan_plan.set_defaults(func=command_scan_plan)

    detect_image = subparsers.add_parser("detect-image", help="Run classical candidate detection on one image.")
    detect_image.add_argument("image_path")
    detect_image.add_argument("--config", required=True)
    detect_image.add_argument("--output-json", required=True)
    detect_image.add_argument("--overlay")
    detect_image.set_defaults(func=command_detect_image)

    flatfield = subparsers.add_parser("build-flatfield", help="Build a flat-field array from blank-field images.")
    flatfield.add_argument("images", nargs="+")
    flatfield.add_argument("--output", required=True)
    flatfield.set_defaults(func=command_build_flatfield)

    replay = subparsers.add_parser("replay-folder", help="Process an image folder into the SQLite catalog.")
    replay.add_argument("image_dir")
    replay.add_argument("--config", required=True)
    replay.add_argument("--catalog", required=True)
    replay.add_argument("--sample-id", required=True)
    replay.add_argument("--material", required=True)
    replay.add_argument("--clusters", type=int, default=4)
    replay.set_defaults(func=command_replay_folder)

    export = subparsers.add_parser("export-coco", help="Export catalog candidates to COCO JSON.")
    export.add_argument("--catalog", required=True)
    export.add_argument("--output", required=True)
    export.add_argument("--score-threshold", type=float, default=0.0)
    export.set_defaults(func=command_export_coco)

    camera_probe = subparsers.add_parser("camera-probe", help="Probe Windows camera connectivity and Canon tooling.")
    camera_probe.add_argument("--output")
    camera_probe.set_defaults(func=command_camera_probe)

    init_session = subparsers.add_parser("init-session", help="Create a reproducible data-collection session scaffold.")
    init_session.add_argument("--config", required=True)
    init_session.add_argument("--output-root", required=True)
    init_session.add_argument("--sample-id", required=True)
    init_session.add_argument("--material", required=True)
    init_session.add_argument("--substrate", required=True)
    init_session.add_argument("--objective", required=True)
    init_session.add_argument("--operator", default="")
    init_session.add_argument("--notes", default="")
    init_session.set_defaults(func=command_init_session)

    estimate_shift = subparsers.add_parser(
        "estimate-shift",
        help="Estimate residual image shift in the overlap between neighboring microscope tiles.",
    )
    estimate_shift.add_argument("reference_image")
    estimate_shift.add_argument("moving_image")
    estimate_shift.add_argument("--axis", choices=["x", "y"], required=True)
    estimate_shift.add_argument("--overlap-fraction", type=float, required=True)
    estimate_shift.add_argument("--output-json")
    estimate_shift.set_defaults(func=command_estimate_shift)

    run_scan = subparsers.add_parser("run-scan", help="Move a raster over a saved scan ROI and capture all tiles.")
    run_scan.add_argument("--config", required=True)
    run_scan.add_argument("--sample-id", required=True)
    run_scan.add_argument("--material", required=True)
    run_scan.add_argument("--substrate", required=True)
    run_scan.add_argument("--objective", required=True)
    run_scan.add_argument("--operator", default="")
    run_scan.add_argument("--notes", default="")
    run_scan.add_argument("--output-root")
    run_scan.add_argument("--roi-min-x-um", type=float)
    run_scan.add_argument("--roi-max-x-um", type=float)
    run_scan.add_argument("--roi-min-y-um", type=float)
    run_scan.add_argument("--roi-max-y-um", type=float)
    run_scan.set_defaults(func=command_run_scan)

    stage_ui = subparsers.add_parser("stage-ui", help="Open the interactive stage calibration UI.")
    stage_ui.add_argument("--config", required=True)
    stage_ui.set_defaults(func=command_stage_ui)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
