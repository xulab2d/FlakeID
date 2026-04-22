from __future__ import annotations

import json
from pathlib import Path

from ..catalog import CatalogStore


def export_catalog_to_coco(catalog_path: str | Path, output_path: str | Path, score_threshold: float = 0.0) -> dict:
    store = CatalogStore(catalog_path)
    rows = store.fetch_candidate_rows()

    images: dict[str, dict] = {}
    annotations: list[dict] = []
    category_names: dict[str, int] = {}

    annotation_id = 1
    for row in rows:
        if float(row["score"]) < score_threshold:
            continue
        image_path = row["image_path"]
        if image_path not in images:
            image_id = len(images) + 1
            images[image_path] = {
                "id": image_id,
                "file_name": image_path,
            }

        category_name = row["review_label"] or row["label"]
        if category_name not in category_names:
            category_names[category_name] = len(category_names) + 1

        annotations.append(
            {
                "id": annotation_id,
                "image_id": images[image_path]["id"],
                "category_id": category_names[category_name],
                "bbox": [row["x_px"], row["y_px"], row["w_px"], row["h_px"]],
                "area": row["area_px"],
                "iscrowd": 0,
                "segmentation": [
                    [
                        row["x_px"],
                        row["y_px"],
                        row["x_px"] + row["w_px"],
                        row["y_px"],
                        row["x_px"] + row["w_px"],
                        row["y_px"] + row["h_px"],
                        row["x_px"],
                        row["y_px"] + row["h_px"],
                    ]
                ],
            }
        )
        annotation_id += 1

    categories = [{"id": identifier, "name": name} for name, identifier in category_names.items()]
    payload = {
        "images": list(images.values()),
        "annotations": annotations,
        "categories": categories,
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload

