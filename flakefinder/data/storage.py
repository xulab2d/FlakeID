from __future__ import annotations

import json
import sqlite3
from dataclasses import astuple
from pathlib import Path

from .schema import CandidateRecord, ScanRecord, TileRecord


class Storage:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS scans (
                scan_id TEXT PRIMARY KEY,
                config_key TEXT,
                mode TEXT,
                input_path TEXT,
                output_dir TEXT,
                model_version TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tiles (
                tile_id TEXT PRIMARY KEY,
                scan_id TEXT,
                x_mm REAL,
                y_mm REAL,
                z_um REAL,
                timestamp_utc TEXT,
                objective TEXT,
                exposure_ms REAL,
                gain REAL,
                illumination_json TEXT,
                config_key TEXT,
                raw_path TEXT,
                preview_path TEXT,
                focus_score REAL,
                qc_passed INTEGER
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS candidates (
                candidate_id TEXT PRIMARY KEY,
                tile_id TEXT,
                bbox_json TEXT,
                centroid_json TEXT,
                predicted_material TEXT,
                predicted_thickness TEXT,
                confidence REAL,
                ranking_score REAL,
                features_json TEXT,
                mask_path TEXT,
                thumbnail_path TEXT,
                review_state TEXT,
                config_version TEXT,
                model_version TEXT
            )
            """
        )
        self.conn.commit()

    def insert_scan(self, scan: ScanRecord) -> None:
        self.conn.execute("INSERT OR REPLACE INTO scans VALUES (?, ?, ?, ?, ?, ?)", astuple(scan))
        self.conn.commit()

    def insert_tile(self, tile: TileRecord) -> None:
        self.conn.execute("INSERT OR REPLACE INTO tiles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", astuple(tile))
        self.conn.commit()

    def insert_candidate(self, candidate: CandidateRecord) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO candidates VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            astuple(candidate),
        )
        self.conn.commit()

    def export_rows(self, table: str) -> list[dict[str, object]]:
        cur = self.conn.execute(f"SELECT * FROM {table}")
        columns = [column[0] for column in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]

    def close(self) -> None:
        self.conn.close()
