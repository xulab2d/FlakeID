from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class RunDirs:
    root: Path
    raw: Path
    previews: Path
    masks: Path
    thumbnails: Path
    exports: Path
    storage: Path
    database_path: Path


def prepare_run_dirs(output_dir: str | Path) -> RunDirs:
    root = Path(output_dir)
    raw = root / "raw"
    previews = root / "previews"
    masks = root / "masks"
    thumbnails = root / "thumbnails"
    exports = root / "exports"
    storage = root / "storage"
    for path in [root, raw, previews, masks, thumbnails, exports, storage]:
        path.mkdir(parents=True, exist_ok=True)
    return RunDirs(
        root=root,
        raw=raw,
        previews=previews,
        masks=masks,
        thumbnails=thumbnails,
        exports=exports,
        storage=storage,
        database_path=storage / "flakefinder.db",
    )
