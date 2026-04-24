import unittest

import numpy as np

from flake_ml.registration import estimate_overlap_shift, phase_correlation_shift


class RegistrationTests(unittest.TestCase):
    def test_phase_correlation_recovers_known_shift(self) -> None:
        rng = np.random.default_rng(123)
        image = rng.random((64, 64), dtype=np.float32)
        shifted = np.roll(image, shift=(4, -6), axis=(0, 1))

        estimate = phase_correlation_shift(image, shifted)
        self.assertAlmostEqual(estimate.dx_px, 6.0, delta=0.5)
        self.assertAlmostEqual(estimate.dy_px, -4.0, delta=0.5)

    def test_overlap_shift_estimates_horizontal_residual(self) -> None:
        rng = np.random.default_rng(456)
        canvas = rng.random((96, 224), dtype=np.float32)
        reference = canvas[:, 0:128]
        moving = canvas[:, 92:220]

        estimate = estimate_overlap_shift(reference, moving, axis="x", overlap_fraction=0.25)
        self.assertAlmostEqual(estimate.dx_px, -4.0, delta=0.5)
        self.assertAlmostEqual(estimate.dy_px, 0.0, delta=0.5)


if __name__ == "__main__":
    unittest.main()
