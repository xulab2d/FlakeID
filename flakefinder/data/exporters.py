from __future__ import annotations

from pathlib import Path

import pandas as pd

from .storage import Storage


def export_candidates(storage: Storage, output_dir: str | Path, file_format: str) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    rows = storage.export_rows("candidates")
    frame = pd.DataFrame(rows)
    if file_format == "csv":
        target = output_path / "candidates.csv"
        frame.to_csv(target, index=False)
        return target
    if file_format == "parquet":
        target = output_path / "candidates.parquet"
        frame.to_parquet(target, index=False)
        return target
    raise ValueError(f"Unsupported export format: {file_format}")
