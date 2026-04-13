from __future__ import annotations

from pathlib import Path

from flakefinder.acquisition.serpentine_scan import generate_serpentine_tiles
from flakefinder.config.loader import load_app_config
from flakefinder.hardware.mock_adapter import MockHardware

from .shared import run_pipeline


def run_mock_scan(config_path: str, input_dir: str, output_dir: str) -> dict[str, object]:
    config = load_app_config(config_path)
    hardware = MockHardware(input_dir)
    planner_tiles = generate_serpentine_tiles(config)
    image_paths = hardware.source_path and sorted(hardware.source_path.iterdir()) or []
    tile_paths = [path for path in image_paths if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".npy"}]
    if planner_tiles:
        tile_paths = tile_paths[: len(planner_tiles)]
    return run_pipeline(
        config=config,
        tile_paths=tile_paths,
        input_path=Path(input_dir),
        output_dir=Path(output_dir),
        mode="mock-scan",
        planned_tiles=planner_tiles,
    )
