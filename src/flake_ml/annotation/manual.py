from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

from ..utils import ensure_dir, timestamp_utc


VALID_TILE_LABELS = (
    "unreviewed",
    "no_flake",
    "graphene",
    "hbn",
    "mixed",
    "artifact",
    "unsure",
)


@dataclass(slots=True)
class ManualObjectAnnotation:
    label: str
    bbox_xywh: tuple[int, int, int, int]

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "bbox_xywh": list(self.bbox_xywh),
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "ManualObjectAnnotation":
        bbox = payload.get("bbox_xywh", [0, 0, 0, 0])
        return cls(
            label=str(payload.get("label", "flake")),
            bbox_xywh=(int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])),
        )


@dataclass(slots=True)
class ManualImageAnnotation:
    image_path: str
    tile_label: str = "unreviewed"
    notes: str = ""
    objects: list[ManualObjectAnnotation] = field(default_factory=list)
    updated_utc: str = ""

    def to_dict(self) -> dict:
        return {
            "image_path": self.image_path,
            "tile_label": self.tile_label,
            "notes": self.notes,
            "objects": [item.to_dict() for item in self.objects],
            "updated_utc": self.updated_utc,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "ManualImageAnnotation":
        return cls(
            image_path=str(payload.get("image_path", "")),
            tile_label=str(payload.get("tile_label", "unreviewed")),
            notes=str(payload.get("notes", "")),
            objects=[ManualObjectAnnotation.from_dict(item) for item in payload.get("objects", [])],
            updated_utc=str(payload.get("updated_utc", "")),
        )


def discover_images(image_root: str | Path) -> list[Path]:
    root = Path(image_root)
    suffixes = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}
    return sorted(path for path in root.iterdir() if path.is_file() and path.suffix.lower() in suffixes)


def resolve_review_paths(
    session_dir: str | Path | None = None,
    image_dir: str | Path | None = None,
    output_path: str | Path | None = None,
) -> tuple[Path, Path]:
    if session_dir is not None:
        session_root = Path(session_dir).resolve()
        resolved_image_dir = session_root / "tiles"
        resolved_output = Path(output_path).resolve() if output_path else session_root / "labels" / "manual_annotations.json"
        return resolved_image_dir, resolved_output
    if image_dir is None:
        raise ValueError("Provide either session_dir or image_dir.")
    resolved_image_dir = Path(image_dir).resolve()
    resolved_output = Path(output_path).resolve() if output_path else resolved_image_dir / "manual_annotations.json"
    return resolved_image_dir, resolved_output


def load_manual_annotations(path: str | Path) -> dict[str, ManualImageAnnotation]:
    source = Path(path)
    if not source.exists():
        return {}
    payload = json.loads(source.read_text(encoding="utf-8"))
    rows = payload.get("annotations", {})
    return {
        image_path: ManualImageAnnotation.from_dict(item)
        for image_path, item in rows.items()
    }


def save_manual_annotations(
    path: str | Path,
    annotations: dict[str, ManualImageAnnotation],
    image_root: str | Path,
) -> None:
    target = Path(path)
    ensure_dir(target.parent)
    payload = {
        "version": 1,
        "image_root": str(Path(image_root).resolve()),
        "updated_utc": timestamp_utc(),
        "annotations": {
            image_path: annotation.to_dict()
            for image_path, annotation in sorted(annotations.items())
        },
    }
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def export_manual_annotations_to_coco(
    review_path: str | Path,
    output_path: str | Path,
    include_unlabeled_images: bool = False,
) -> dict:
    annotations = load_manual_annotations(review_path)
    images: list[dict] = []
    objects: list[dict] = []
    categories: dict[str, int] = {}
    image_id = 1
    annotation_id = 1

    for image_path, annotation in sorted(annotations.items()):
        if not annotation.objects and not include_unlabeled_images:
            continue
        images.append({"id": image_id, "file_name": image_path})
        for item in annotation.objects:
            if item.label not in categories:
                categories[item.label] = len(categories) + 1
            x, y, w, h = item.bbox_xywh
            objects.append(
                {
                    "id": annotation_id,
                    "image_id": image_id,
                    "category_id": categories[item.label],
                    "bbox": [x, y, w, h],
                    "area": w * h,
                    "iscrowd": 0,
                    "segmentation": [[x, y, x + w, y, x + w, y + h, x, y + h]],
                }
            )
            annotation_id += 1
        image_id += 1

    payload = {
        "images": images,
        "annotations": objects,
        "categories": [{"id": category_id, "name": name} for name, category_id in categories.items()],
    }
    target = Path(output_path)
    ensure_dir(target.parent)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
