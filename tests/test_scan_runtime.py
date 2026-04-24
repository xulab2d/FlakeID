import json
import unittest
from pathlib import Path

from flake_ml.config import load_lab_config
from flake_ml.models import StagePosition
from flake_ml.motion.base import MotionController
from flake_ml.scanning.runtime import build_scan_tiles_from_roi, run_capture_scan


class FakeMotionController(MotionController):
    def __init__(self) -> None:
        self.position = StagePosition(0.0, 0.0)
        self.moves: list[tuple[float, float]] = []

    def home(self) -> None:
        self.position = StagePosition(0.0, 0.0)

    def move_abs(self, x_um: float, y_um: float) -> None:
        self.position = StagePosition(x_um, y_um)
        self.moves.append((x_um, y_um))

    def wait_for_idle(self) -> None:
        return None

    def current_position(self) -> StagePosition:
        return self.position


class FakeCamera:
    def __init__(self) -> None:
        self.captures: list[Path] = []

    def capture(self, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fake-image")
        self.captures.append(path)
        return path


class ScanRuntimeTests(unittest.TestCase):
    def test_build_scan_tiles_from_roi_sorts_bounds(self) -> None:
        config = load_lab_config(Path.cwd() / "configs" / "lab.example.toml")
        config.scan.fov_width_um = 200.0
        config.scan.fov_height_um = 200.0
        config.scan.overlap_fraction = 0.0
        config.motion.min_x_um = 0.0
        config.motion.min_y_um = 0.0
        config.motion.max_x_um = 2000.0
        config.motion.max_y_um = 2000.0
        config.motion.safety_margin_um = 0.0

        tiles = build_scan_tiles_from_roi(700.0, 100.0, 800.0, 200.0, config)
        self.assertEqual((tiles[0].position.x_um, tiles[0].position.y_um), (100.0, 200.0))

    def test_run_capture_scan_creates_session_and_images(self) -> None:
        config_path = Path.cwd() / "configs" / "lab.example.toml"
        config = load_lab_config(config_path)
        config.scan.fov_width_um = 200.0
        config.scan.fov_height_um = 200.0
        config.scan.overlap_fraction = 0.0
        config.motion.min_x_um = 0.0
        config.motion.min_y_um = 0.0
        config.motion.max_x_um = 2000.0
        config.motion.max_y_um = 2000.0
        config.motion.safety_margin_um = 0.0

        output_root = Path.cwd() / "outputs" / "test_temp" / "scan_runtime"
        motion = FakeMotionController()
        camera = FakeCamera()

        summary = run_capture_scan(
            config_path=config_path,
            config=config,
            sample_id="scan_runtime",
            material="graphene",
            substrate="graphene_285_wet",
            objective="10x",
            operator="tester",
            notes="",
            roi_min_x_um=100.0,
            roi_max_x_um=600.0,
            roi_min_y_um=200.0,
            roi_max_y_um=700.0,
            output_root=output_root,
            motion=motion,
            camera=camera,
        )

        session_dir = Path(summary["session_dir"])
        self.assertTrue(session_dir.exists())
        self.assertTrue((session_dir / "scan_catalog.db").exists())
        self.assertTrue((session_dir / "qc" / "scan_plan.json").exists())
        summary_payload = json.loads((session_dir / "qc" / "scan_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary_payload["tile_count"], 9)
        self.assertEqual(len(camera.captures), 9)
        self.assertEqual(len(motion.moves), 9)


if __name__ == "__main__":
    unittest.main()
