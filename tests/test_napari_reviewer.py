import unittest
from pathlib import Path

from flake_ml.annotation.manual import ManualImageAnnotation
from flake_ml.ui.napari_reviewer import (
    _find_resume_index,
    _normalize_object_label,
    _resolve_jump_index,
    _sanitize_shape_labels,
)


class NapariReviewerTests(unittest.TestCase):
    def test_normalize_object_label_replaces_none_and_invalid_values(self) -> None:
        self.assertEqual(_normalize_object_label(None, "graphene"), "graphene")
        self.assertEqual(_normalize_object_label("None", "hbn"), "hbn")
        self.assertEqual(_normalize_object_label("artifact", "graphene"), "artifact")
        self.assertEqual(_normalize_object_label("mystery", "other_flake"), "other_flake")

    def test_sanitize_shape_labels_fills_missing_rows(self) -> None:
        labels = _sanitize_shape_labels(["graphene", None], count=4, fallback="hbn")
        self.assertEqual(labels, ["graphene", "hbn", "hbn", "hbn"])

    def test_find_resume_index_prefers_latest_updated_annotation(self) -> None:
        images = [
            Path("tile_001.jpg"),
            Path("tile_002.jpg"),
            Path("tile_003.jpg"),
        ]
        annotations = {
            str(images[0].resolve()): ManualImageAnnotation(
                image_path=str(images[0].resolve()),
                updated_utc="2026-04-24T03:00:00+00:00",
            ),
            str(images[2].resolve()): ManualImageAnnotation(
                image_path=str(images[2].resolve()),
                updated_utc="2026-04-24T04:00:00+00:00",
            ),
        }
        self.assertEqual(_find_resume_index(images, annotations), 2)

    def test_resolve_jump_index_supports_number_and_filename(self) -> None:
        images = [
            Path("tile_r001_c000_x100_y100.jpg"),
            Path("tile_r001_c001_x200_y100.jpg"),
            Path("tile_r001_c002_x300_y100.jpg"),
        ]
        index_by_number, error_by_number = _resolve_jump_index(images, "2")
        self.assertEqual(index_by_number, 1)
        self.assertIsNone(error_by_number)

        index_by_name, error_by_name = _resolve_jump_index(images, "c002")
        self.assertEqual(index_by_name, 2)
        self.assertIsNone(error_by_name)

        missing_index, missing_error = _resolve_jump_index(images, "does-not-exist")
        self.assertIsNone(missing_index)
        self.assertIn("No image name contains", missing_error)


if __name__ == "__main__":
    unittest.main()
