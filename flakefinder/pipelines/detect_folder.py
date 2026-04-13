from __future__ import annotations

from pathlib import Path

from flakefinder.acquisition.tiling import enumerate_folder_tiles
from flakefinder.config.loader import load_app_config

from .shared import run_pipeline


def run_detect_folder(config_path: str, input_dir: str, output_dir: str) -> dict[str, object]:
    config = load_app_config(config_path)
    tile_paths = enumerate_folder_tiles(input_dir)
    return run_pipeline(config=config, tile_paths=tile_paths, input_path=Path(input_dir), output_dir=Path(output_dir), mode="detect-folder")
