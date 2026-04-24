import json
import unittest
from pathlib import Path

from flake_ml.annotation.manual import (
    ManualImageAnnotation,
    ManualObjectAnnotation,
    export_manual_annotations_to_coco,
    load_manual_annotations,
    normalize_tile_label,
    resolve_review_paths,
    save_manual_annotations,
)


class ManualAnnotationTests(unittest.TestCase):
    def test_normalize_tile_label_maps_legacy_values(self) -> None:
        self.assertEqual(normalize_tile_label("no_flake"), "empty_substrate")
        self.assertEqual(normalize_tile_label("graphene"), "flake_present")
        self.assertEqual(normalize_tile_label("hbn"), "flake_present")
        self.assertEqual(normalize_tile_label("mixed"), "flake_present")
        self.assertEqual(normalize_tile_label("bad_focus"), "bad_focus")

    def test_resolve_review_paths_for_session_dir(self) -> None:
        session_dir = Path.cwd() / "outputs" / "test_temp" / "manual_review" / "session_a"
        image_dir, output_path = resolve_review_paths(session_dir=session_dir)
        self.assertEqual(image_dir, session_dir.resolve() / "tiles")
        self.assertEqual(output_path, session_dir.resolve() / "labels" / "manual_annotations.json")

    def test_save_and_export_manual_annotations(self) -> None:
        workspace = Path.cwd() / "outputs" / "test_temp" / "manual_review"
        image_root = workspace / "tiles"
        image_root.mkdir(parents=True, exist_ok=True)
        review_path = workspace / "labels" / "manual_annotations.json"

        image_a = image_root / "tile_a.jpg"
        image_b = image_root / "tile_b.jpg"
        image_c = image_root / "tile_c.jpg"
        image_a.write_bytes(b"a")
        image_b.write_bytes(b"b")
        image_c.write_bytes(b"c")

        annotations = {
            str(image_a.resolve()): ManualImageAnnotation(
                image_path=str(image_a.resolve()),
                tile_label="flake_present",
                objects=[ManualObjectAnnotation(label="graphene", bbox_xywh=(10, 20, 30, 40))],
            ),
            str(image_b.resolve()): ManualImageAnnotation(
                image_path=str(image_b.resolve()),
                tile_label="flake_present",
                objects=[
                    ManualObjectAnnotation(
                        label="hbn",
                        shape_type="polygon",
                        vertices_xy=[(5, 5), (35, 5), (28, 22), (12, 28)],
                    )
                ],
            ),
            str(image_c.resolve()): ManualImageAnnotation(
                image_path=str(image_c.resolve()),
                tile_label="empty_substrate",
                objects=[],
            ),
        }
        save_manual_annotations(review_path, annotations, image_root=image_root)
        self.assertTrue(review_path.exists())

        reloaded = load_manual_annotations(review_path)
        polygon_object = reloaded[str(image_b.resolve())].objects[0]
        self.assertEqual(polygon_object.shape_type, "polygon")
        self.assertEqual(polygon_object.bbox_xywh, (5, 5, 30, 23))

        coco_path = workspace / "labels" / "manual_annotations.coco.json"
        payload = export_manual_annotations_to_coco(review_path, coco_path)
        self.assertEqual(len(payload["images"]), 2)
        self.assertEqual(len(payload["annotations"]), 2)
        self.assertEqual(payload["categories"][0]["name"], "graphene")
        polygon_annotation = next(
            row
            for row in payload["annotations"]
            if payload["categories"][row["category_id"] - 1]["name"] == "hbn"
        )
        self.assertEqual(len(polygon_annotation["segmentation"][0]), 8)
        self.assertGreater(polygon_annotation["area"], 0.0)

        saved = json.loads(coco_path.read_text(encoding="utf-8"))
        self.assertEqual(len(saved["annotations"]), 2)


if __name__ == "__main__":
    unittest.main()
