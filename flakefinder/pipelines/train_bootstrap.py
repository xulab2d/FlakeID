from __future__ import annotations

from pathlib import Path

from flakefinder.data.coco_io import export_coco
from flakefinder.data.manifest import write_manifest


def run_train_bootstrap(manifest_path: str) -> Path:
    manifest = {
        "datasets": [
            {"config_key": "bn90_hbn", "task": "detection", "notes": "Collect glovebox RAW/16-bit data plus hard negatives."},
            {"config_key": "gr285_graphene", "task": "detection", "notes": "Collect graphene-on-285nm oxide tiles and thickness labels."},
        ],
        "hard_negative_mining": True,
        "manual_review_required": True,
    }
    path = Path(manifest_path)
    write_manifest(manifest, path)
    export_coco({"images": [], "annotations": [], "categories": []}, path.with_suffix(".coco.json"))
    return path
