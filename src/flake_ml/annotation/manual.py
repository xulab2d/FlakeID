from __future__ import annotations

from dataclasses import dataclass, field
import json
from math import ceil, floor
from pathlib import Path
from typing import Iterable

from ..utils import ensure_dir, timestamp_utc


VALID_TILE_LABELS = (
    "unreviewed",
    "flake_present",
    "empty_substrate",
    "off_target",
    "bad_focus",
    "artifact",
    "unsure",
)

LEGACY_TILE_LABEL_ALIASES = {
    "no_flake": "empty_substrate",
    "graphene": "flake_present",
    "hbn": "flake_present",
    "mixed": "flake_present",
}

VALID_OBJECT_LABELS = (
    "graphene",
    "hbn",
    "other_flake",
    "artifact",
)


def normalize_tile_label(value: str) -> str:
    label = str(value or "unreviewed").strip().lower()
    if label in LEGACY_TILE_LABEL_ALIASES:
        return LEGACY_TILE_LABEL_ALIASES[label]
    if label in VALID_TILE_LABELS:
        return label
    return "unreviewed"


def normalize_vertices(vertices_xy: Iterable[Iterable[float]]) -> list[tuple[float, float]]:
    normalized: list[tuple[float, float]] = []
    for vertex in vertices_xy:
        x, y = vertex
        normalized.append((float(x), float(y)))
    return normalized


def rectangle_vertices_from_bbox(bbox_xywh: tuple[int, int, int, int]) -> list[tuple[float, float]]:
    x, y, width, height = bbox_xywh
    return [
        (float(x), float(y)),
        (float(x + width), float(y)),
        (float(x + width), float(y + height)),
        (float(x), float(y + height)),
    ]


def bbox_from_vertices(vertices_xy: Iterable[Iterable[float]]) -> tuple[int, int, int, int]:
    normalized = normalize_vertices(vertices_xy)
    if not normalized:
        return (0, 0, 0, 0)
    xs = [vertex[0] for vertex in normalized]
    ys = [vertex[1] for vertex in normalized]
    min_x = floor(min(xs))
    max_x = ceil(max(xs))
    min_y = floor(min(ys))
    max_y = ceil(max(ys))
    return (int(min_x), int(min_y), int(max_x - min_x), int(max_y - min_y))


def polygon_area(vertices_xy: Iterable[Iterable[float]]) -> float:
    normalized = normalize_vertices(vertices_xy)
    if len(normalized) < 3:
        return 0.0
    area = 0.0
    for index, (x0, y0) in enumerate(normalized):
        x1, y1 = normalized[(index + 1) % len(normalized)]
        area += (x0 * y1) - (x1 * y0)
    return abs(area) * 0.5


@dataclass(slots=True)
class ManualObjectAnnotation:
    label: str
    bbox_xywh: tuple[int, int, int, int] = (0, 0, 0, 0)
    shape_type: str = "bbox"
    vertices_xy: list[tuple[float, float]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.label = str(self.label)
        self.vertices_xy = normalize_vertices(self.vertices_xy)
        inferred_shape_type = "polygon" if self.vertices_xy else "bbox"
        self.shape_type = str(self.shape_type or inferred_shape_type)
        if self.vertices_xy:
            self.bbox_xywh = bbox_from_vertices(self.vertices_xy)
        else:
            x, y, width, height = self.bbox_xywh
            self.bbox_xywh = (int(x), int(y), int(width), int(height))

    def to_dict(self) -> dict:
        payload = {
            "label": self.label,
            "bbox_xywh": list(self.bbox_xywh),
            "shape_type": self.shape_type,
        }
        if self.vertices_xy:
            payload["vertices_xy"] = [[x, y] for x, y in self.vertices_xy]
        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> "ManualObjectAnnotation":
        bbox = payload.get("bbox_xywh", [0, 0, 0, 0])
        raw_vertices = payload.get("vertices_xy", payload.get("polygon_xy", []))
        return cls(
            label=str(payload.get("label", "flake")),
            bbox_xywh=(int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])),
            shape_type=str(payload.get("shape_type", "polygon" if raw_vertices else "bbox")),
            vertices_xy=raw_vertices,
        )

    @property
    def display_vertices_xy(self) -> list[tuple[float, float]]:
        if self.vertices_xy:
            return self.vertices_xy
        return rectangle_vertices_from_bbox(self.bbox_xywh)

    @property
    def segmentation_xy(self) -> list[float]:
        flattened: list[float] = []
        for x, y in self.display_vertices_xy:
            flattened.extend([float(x), float(y)])
        return flattened

    @property
    def area_px(self) -> float:
        if self.vertices_xy:
            area = polygon_area(self.vertices_xy)
            if area > 0:
                return area
        _, _, width, height = self.bbox_xywh
        return float(max(0, width) * max(0, height))


@dataclass(slots=True)
class ManualImageAnnotation:
    image_path: str
    tile_label: str = "unreviewed"
    notes: str = ""
    objects: list[ManualObjectAnnotation] = field(default_factory=list)
    updated_utc: str = ""

    def __post_init__(self) -> None:
        self.image_path = str(self.image_path)
        self.tile_label = normalize_tile_label(self.tile_label)
        self.notes = str(self.notes)
        self.updated_utc = str(self.updated_utc)

    def to_dict(self) -> dict:
        return {
            "image_path": self.image_path,
            "tile_label": normalize_tile_label(self.tile_label),
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
        "version": 2,
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
                    "area": item.area_px,
                    "iscrowd": 0,
                    "segmentation": [item.segmentation_xy],
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
