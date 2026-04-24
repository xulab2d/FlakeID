import unittest

from flake_ml.ui.napari_reviewer import _normalize_object_label, _sanitize_shape_labels


class NapariReviewerTests(unittest.TestCase):
    def test_normalize_object_label_replaces_none_and_invalid_values(self) -> None:
        self.assertEqual(_normalize_object_label(None, "graphene"), "graphene")
        self.assertEqual(_normalize_object_label("None", "hbn"), "hbn")
        self.assertEqual(_normalize_object_label("artifact", "graphene"), "artifact")
        self.assertEqual(_normalize_object_label("mystery", "other_flake"), "other_flake")

    def test_sanitize_shape_labels_fills_missing_rows(self) -> None:
        labels = _sanitize_shape_labels(["graphene", None], count=4, fallback="hbn")
        self.assertEqual(labels, ["graphene", "hbn", "hbn", "hbn"])


if __name__ == "__main__":
    unittest.main()
