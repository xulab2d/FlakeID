from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sqlite3
from typing import Iterable

from .models import FlakeCandidate, ScanTile
from .utils import timestamp_utc


class CatalogStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def init(self) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sample_id TEXT NOT NULL,
                    material TEXT NOT NULL,
                    config_path TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER NOT NULL,
                    tile_index INTEGER NOT NULL,
                    row_index INTEGER NOT NULL,
                    column_index INTEGER NOT NULL,
                    stage_x_um REAL NOT NULL,
                    stage_y_um REAL NOT NULL,
                    width_um REAL NOT NULL,
                    height_um REAL NOT NULL,
                    image_path TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    FOREIGN KEY(scan_id) REFERENCES scans(id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER NOT NULL,
                    tile_index INTEGER NOT NULL,
                    image_path TEXT NOT NULL,
                    x_px INTEGER NOT NULL,
                    y_px INTEGER NOT NULL,
                    w_px INTEGER NOT NULL,
                    h_px INTEGER NOT NULL,
                    area_px INTEGER NOT NULL,
                    score REAL NOT NULL,
                    label TEXT NOT NULL,
                    cluster_id INTEGER,
                    review_label TEXT,
                    features_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(scan_id) REFERENCES scans(id)
                )
                """
            )
            connection.commit()

    def create_scan(self, sample_id: str, material: str, config_path: str | None = None) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO scans (sample_id, material, config_path, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (sample_id, material, config_path, timestamp_utc()),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def record_tile(self, scan_id: int, tile: ScanTile) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO tiles (
                    scan_id, tile_index, row_index, column_index, stage_x_um, stage_y_um,
                    width_um, height_um, image_path, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scan_id,
                    tile.index,
                    tile.row,
                    tile.column,
                    tile.position.x_um,
                    tile.position.y_um,
                    tile.width_um,
                    tile.height_um,
                    tile.image_path or "",
                    json.dumps(tile.metadata),
                ),
            )
            connection.commit()

    def record_candidates(self, scan_id: int, image_path: str, candidates: Iterable[FlakeCandidate]) -> None:
        rows = [
            (
                scan_id,
                candidate.tile_index,
                image_path,
                candidate.bbox_xywh[0],
                candidate.bbox_xywh[1],
                candidate.bbox_xywh[2],
                candidate.bbox_xywh[3],
                candidate.area_px,
                candidate.score,
                candidate.label,
                candidate.cluster_id,
                json.dumps(candidate.features),
                timestamp_utc(),
            )
            for candidate in candidates
        ]
        if not rows:
            return
        with self.connect() as connection:
            connection.executemany(
                """
                INSERT INTO candidates (
                    scan_id, tile_index, image_path, x_px, y_px, w_px, h_px, area_px,
                    score, label, cluster_id, features_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            connection.commit()

    def update_clusters(self, assignments: dict[int, int]) -> None:
        with self.connect() as connection:
            for candidate_id, cluster_id in assignments.items():
                connection.execute(
                    "UPDATE candidates SET cluster_id = ? WHERE id = ?",
                    (cluster_id, candidate_id),
                )
            connection.commit()

    def update_review(self, candidate_id: int, review_label: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE candidates SET review_label = ? WHERE id = ?",
                (review_label, candidate_id),
            )
            connection.commit()

    def fetch_candidate_rows(self, scan_id: int | None = None) -> list[sqlite3.Row]:
        with self.connect() as connection:
            if not self._has_table(connection, "candidates"):
                raise RuntimeError(
                    f"Catalog {self.path} is not initialized. Run a scan or replay-folder before exporting."
                )
            connection.row_factory = sqlite3.Row
            if scan_id is None:
                cursor = connection.execute("SELECT * FROM candidates ORDER BY id")
            else:
                cursor = connection.execute("SELECT * FROM candidates WHERE scan_id = ? ORDER BY id", (scan_id,))
            return list(cursor.fetchall())

    def fetch_training_rows(self) -> list[sqlite3.Row]:
        with self.connect() as connection:
            if not self._has_table(connection, "candidates"):
                raise RuntimeError(
                    f"Catalog {self.path} is not initialized. Run a scan or replay-folder before reading training rows."
                )
            connection.row_factory = sqlite3.Row
            cursor = connection.execute(
                "SELECT * FROM candidates WHERE review_label IS NOT NULL ORDER BY id"
            )
            return list(cursor.fetchall())

    @staticmethod
    def _has_table(connection: sqlite3.Connection, table_name: str) -> bool:
        cursor = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        )
        return cursor.fetchone() is not None
