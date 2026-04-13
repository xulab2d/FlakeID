from __future__ import annotations

from pathlib import Path

from flakefinder.imaging.raw_io import supported_image_files


def enumerate_folder_tiles(input_dir: str | Path) -> list[Path]:
    return sorted(path for path in Path(input_dir).iterdir() if path.suffix.lower() in supported_image_files())
