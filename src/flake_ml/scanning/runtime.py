from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import time
from typing import Callable

from ..acquisition import Camera, DirectoryReplayCamera, ExternalCommandCamera, WatchedFolderCamera
from ..catalog import CatalogStore
from ..config import LabConfig
from ..models import ScanTile, StagePosition
from ..motion import DryRunMotionController
from ..motion.base import MotionController
from ..motion.grbl_bridge import GrblStatus, PowerShellGrblBridge
from ..scanning.planner import build_serpentine_plan
from ..session import initialize_session
from ..utils import ensure_dir, resolve_path, timestamp_utc


LogCallback = Callable[[str], None]


def _write_json(path: str | Path, payload: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _validate_tiles_within_motion_bounds(tiles: list[ScanTile], config: LabConfig) -> None:
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
    safe_min_x = min_x_um + margin_um
    safe_min_y = min_y_um + margin_um

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
        raise ValueError(
            "Scan plan falls outside configured safe motion bounds. " + "; ".join(failures)
        )


def build_scan_tiles_from_roi(
    min_x_um: float,
    max_x_um: float,
    min_y_um: float,
    max_y_um: float,
    config: LabConfig,
    enforce_bounds: bool = True,
) -> list[ScanTile]:
    left_x_um = float(min(min_x_um, max_x_um))
    right_x_um = float(max(min_x_um, max_x_um))
    top_y_um = float(min(min_y_um, max_y_um))
    bottom_y_um = float(max(min_y_um, max_y_um))

    tiles = build_serpentine_plan(
        width_um=max(right_x_um - left_x_um, 1.0),
        height_um=max(bottom_y_um - top_y_um, 1.0),
        fov_width_um=config.scan.fov_width_um,
        fov_height_um=config.scan.fov_height_um,
        overlap_fraction=config.scan.overlap_fraction,
        origin_x_um=left_x_um,
        origin_y_um=top_y_um,
    )
    if enforce_bounds:
        _validate_tiles_within_motion_bounds(tiles, config)
    return tiles


@dataclass(slots=True)
class MachineSpacePowerShellMotionController(MotionController):
    port: str
    baud: int
    travel_rate_um_s: float
    settle_time_ms: int
    startup_delay_ms: int = 500
    bridge: PowerShellGrblBridge = field(init=False)

    def __post_init__(self) -> None:
        self.bridge = PowerShellGrblBridge(self.port, baud=self.baud, startup_delay_ms=self.startup_delay_ms)

    def home(self) -> None:
        self.bridge.run_lines(["$H"], wait_for="ok", timeout_ms=20000)

    def _status(self) -> GrblStatus:
        return self.bridge.status()

    def unlock_if_needed(self) -> None:
        status = self._status()
        if status.state == "Alarm":
            self.bridge.unlock()
            self.wait_for_idle()

    def move_abs(self, x_um: float, y_um: float) -> None:
        status = self._status()
        offset_x_mm = status.machine_x_mm - status.work_x_mm
        offset_y_mm = status.machine_y_mm - status.work_y_mm
        work_x_mm = (x_um / 1000.0) - offset_x_mm
        work_y_mm = (y_um / 1000.0) - offset_y_mm
        feed_mm_min = max((self.travel_rate_um_s * 60.0) / 1000.0, 0.1)
        self.bridge.run_lines(
            ["G21", "G90", f"G1 X{work_x_mm:.4f} Y{work_y_mm:.4f} F{feed_mm_min:.2f}"],
            wait_for="ok",
            timeout_ms=6000,
        )
        self.wait_for_idle()

    def wait_for_idle(self) -> None:
        deadline = time.time() + 30.0
        while time.time() < deadline:
            status = self._status()
            if status.state == "Idle":
                time.sleep(self.settle_time_ms / 1000.0)
                return
            time.sleep(0.05)
        raise TimeoutError("GRBL did not return to Idle before timeout.")

    def current_position(self) -> StagePosition:
        status = self._status()
        return StagePosition(status.machine_x_mm * 1000.0, status.machine_y_mm * 1000.0)


def build_camera_from_config(config: LabConfig, repo_root: str | Path) -> Camera:
    driver = config.camera.driver.lower().strip()
    incoming_dir = config.camera.incoming_dir or "photos/incoming"
    incoming_path = resolve_path(incoming_dir, base_dir=repo_root)

    if driver == "external_command":
        if not config.camera.capture_command.strip():
            raise ValueError("camera.capture_command is empty. Configure a real external capture command first.")
        return ExternalCommandCamera(config.camera.capture_command)
    if driver == "watched_folder":
        ensure_dir(incoming_path)
        return WatchedFolderCamera(
            incoming_dir=incoming_path,
            trigger_command_template=config.camera.capture_command,
            timeout_s=config.camera.watch_timeout_s,
            stability_ms=config.camera.watch_stability_ms,
            watch_extensions=config.camera.watch_extensions,
        )
    if driver == "directory_replay":
        return DirectoryReplayCamera(incoming_path)
    raise ValueError(f"Unsupported camera driver: {config.camera.driver!r}")


def run_capture_scan(
    config_path: str | Path,
    config: LabConfig,
    sample_id: str,
    material: str,
    substrate: str,
    objective: str,
    operator: str,
    notes: str,
    roi_min_x_um: float,
    roi_max_x_um: float,
    roi_min_y_um: float,
    roi_max_y_um: float,
    output_root: str | Path,
    allow_out_of_bounds: bool = False,
    motion: MotionController | None = None,
    camera: Camera | None = None,
    log: LogCallback | None = None,
) -> dict:
    repo_root = Path(config_path).resolve().parents[1]
    output_root_path = resolve_path(output_root, base_dir=repo_root)
    manifest = initialize_session(
        output_root=output_root_path,
        config_path=config_path,
        config=config,
        sample_id=sample_id,
        material=material,
        substrate=substrate,
        objective=objective,
        operator=operator,
        notes=notes,
    )
    session_dir = Path(manifest["config_snapshot"]).parent
    tiles_dir = Path(manifest["paths"]["tiles"])
    logs_dir = Path(manifest["paths"]["logs"])
    qc_dir = Path(manifest["paths"]["qc"])
    catalog_path = session_dir / "scan_catalog.db"
    log_path = logs_dir / "scan.log.jsonl"
    plan_path = qc_dir / "scan_plan.json"
    hot_folder = resolve_path(config.camera.incoming_dir or "photos/incoming", base_dir=repo_root)
    step_x_um = max(config.scan.fov_width_um * (1.0 - config.scan.overlap_fraction), 1.0)
    step_y_um = max(config.scan.fov_height_um * (1.0 - config.scan.overlap_fraction), 1.0)

    tiles = build_scan_tiles_from_roi(
        roi_min_x_um,
        roi_max_x_um,
        roi_min_y_um,
        roi_max_y_um,
        config,
        enforce_bounds=not allow_out_of_bounds,
    )
    _write_json(
        plan_path,
        {
            "count": len(tiles),
            "roi_min_x_um": min(roi_min_x_um, roi_max_x_um),
            "roi_max_x_um": max(roi_min_x_um, roi_max_x_um),
            "roi_min_y_um": min(roi_min_y_um, roi_max_y_um),
            "roi_max_y_um": max(roi_min_y_um, roi_max_y_um),
            "allow_out_of_bounds": allow_out_of_bounds,
            "tiles": [tile.to_dict() for tile in tiles],
        },
    )

    if motion is None:
        motion = MachineSpacePowerShellMotionController(
            port=config.motion.port,
            baud=config.motion.baud,
            travel_rate_um_s=config.motion.travel_rate_um_s,
            settle_time_ms=config.motion.settle_time_ms,
            startup_delay_ms=config.motion.startup_delay_ms,
        )
    if camera is None:
        camera = build_camera_from_config(config, repo_root=repo_root)

    if isinstance(motion, MachineSpacePowerShellMotionController):
        motion.unlock_if_needed()

    store = CatalogStore(catalog_path)
    store.init()
    scan_id = store.create_scan(sample_id=sample_id, material=material, config_path=str(Path(config_path).resolve()))

    if log:
        log(f"Session: {session_dir}")
        log(f"Planned tiles: {len(tiles)}")
        log(f"Catalog: {catalog_path}")
        log(
            "Scan ROI: X={0:.1f}..{1:.1f} um, Y={2:.1f}..{3:.1f} um; "
            "step size about {4:.1f} x {5:.1f} um".format(
                min(roi_min_x_um, roi_max_x_um),
                max(roi_min_x_um, roi_max_x_um),
                min(roi_min_y_um, roi_max_y_um),
                max(roi_min_y_um, roi_max_y_um),
                step_x_um,
                step_y_um,
            )
        )
        if allow_out_of_bounds:
            log("Safe motion bounds are being bypassed for this scan. Proceed carefully.")
        if config.camera.driver.lower().strip() == "watched_folder":
            log(f"Watched incoming folder: {hot_folder}")
            if not config.camera.capture_command.strip():
                log("No capture command configured; capture will wait for a new file in the watched folder at each tile.")

    with log_path.open("a", encoding="utf-8") as handle:
        for tile in tiles:
            if log:
                log(
                    f"Moving to tile {tile.index + 1}/{len(tiles)} "
                    f"at X={tile.position.x_um:.1f} um, Y={tile.position.y_um:.1f} um"
                )
            motion.move_abs(tile.position.x_um, tile.position.y_um)
            image_path = tiles_dir / (
                f"tile_r{tile.row:03d}_c{tile.column:03d}_x{int(round(tile.position.x_um))}_y{int(round(tile.position.y_um))}"
                f"{config.camera.output_extension}"
            )
            if log and config.camera.driver.lower().strip() == "watched_folder" and not config.camera.capture_command.strip():
                log(f"Waiting for a new image in {hot_folder} for tile {tile.index + 1}/{len(tiles)}.")
            captured_path = camera.capture(image_path)
            tile.image_path = str(Path(captured_path).resolve())
            tile.metadata = {
                "captured_utc": timestamp_utc(),
                "sample_id": sample_id,
                "material": material,
                "substrate": substrate,
                "objective": objective,
            }
            store.record_tile(scan_id, tile)
            event = {
                "event": "captured",
                "tile_index": tile.index,
                "row": tile.row,
                "column": tile.column,
                "stage_x_um": tile.position.x_um,
                "stage_y_um": tile.position.y_um,
                "image_path": tile.image_path,
                "captured_utc": tile.metadata["captured_utc"],
            }
            handle.write(json.dumps(event) + "\n")
            handle.flush()
            if log:
                log(
                    f"Captured tile {tile.index + 1}/{len(tiles)} "
                    f"(row {tile.row}, col {tile.column}) -> {image_path.name}"
                )

    summary = {
        "session_dir": str(session_dir.resolve()),
        "scan_id": scan_id,
        "tile_count": len(tiles),
        "catalog_path": str(catalog_path.resolve()),
        "plan_path": str(plan_path.resolve()),
        "log_path": str(log_path.resolve()),
    }
    (qc_dir / "scan_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
