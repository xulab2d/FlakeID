import json
import unittest
from pathlib import Path

from flake_ml.annotation.manual import (
    ManualImageAnnotation,
    ManualObjectAnnotation,
    export_manual_annotations_to_coco,
    resolve_review_paths,
    save_manual_annotations,
)


class ManualAnnotationTests(unittest.TestCase):
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
        image_a.write_bytes(b"a")
        image_b.write_bytes(b"b")

        annotations = {
            str(image_a.resolve()): ManualImageAnnotation(
                image_path=str(image_a.resolve()),
                tile_label="graphene",
                objects=[ManualObjectAnnotation(label="graphene", bbox_xywh=(10, 20, 30, 40))],
            ),
            str(image_b.resolve()): ManualImageAnnotation(
                image_path=str(image_b.resolve()),
                tile_label="no_flake",
                objects=[],
            ),
        }
        save_manual_annotations(review_path, annotations, image_root=image_root)
        self.assertTrue(review_path.exists())

        coco_path = workspace / "labels" / "manual_annotations.coco.json"
        payload = export_manual_annotations_to_coco(review_path, coco_path)
        self.assertEqual(len(payload["images"]), 1)
        self.assertEqual(len(payload["annotations"]), 1)
        self.assertEqual(payload["categories"][0]["name"], "graphene")

        saved = json.loads(coco_path.read_text(encoding="utf-8"))
        self.assertEqual(len(saved["annotations"]), 1)


if __name__ == "__main__":
    unittest.main()
