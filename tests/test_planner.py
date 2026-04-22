import unittest

from flake_ml.scanning.planner import build_serpentine_plan


class PlannerTests(unittest.TestCase):
    def test_serpentine_order_reverses_on_odd_rows(self) -> None:
        plan = build_serpentine_plan(
            width_um=500.0,
            height_um=500.0,
            fov_width_um=200.0,
            fov_height_um=200.0,
            overlap_fraction=0.0,
        )
        first_row = [(tile.row, tile.column) for tile in plan[:3]]
        second_row = [(tile.row, tile.column) for tile in plan[3:6]]
        self.assertEqual(first_row, [(0, 0), (0, 1), (0, 2)])
        self.assertEqual(second_row, [(1, 2), (1, 1), (1, 0)])


if __name__ == "__main__":
    unittest.main()

