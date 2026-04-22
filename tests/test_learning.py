import unittest

import numpy as np

from flake_ml.learning.gmm import GaussianMixtureModel
from flake_ml.learning.logistic import LogisticRegressor


class LearningTests(unittest.TestCase):
    def test_gmm_separates_two_clusters(self) -> None:
        rng = np.random.default_rng(0)
        cluster_a = rng.normal(loc=[0.0, 0.0], scale=0.2, size=(50, 2))
        cluster_b = rng.normal(loc=[3.0, 3.0], scale=0.2, size=(50, 2))
        X = np.vstack([cluster_a, cluster_b]).astype(np.float32)
        model = GaussianMixtureModel(n_components=2, max_iter=200).fit(X)
        labels = model.predict(X)
        self.assertEqual(len(np.unique(labels)), 2)

    def test_logistic_regression_learns_simple_boundary(self) -> None:
        X = np.array(
            [
                [0.0, 0.0],
                [0.2, 0.1],
                [1.0, 1.0],
                [1.2, 0.9],
            ],
            dtype=np.float32,
        )
        y = np.array([0, 0, 1, 1], dtype=np.float32)
        model = LogisticRegressor(learning_rate=0.3, epochs=800).fit(X, y)
        predictions = model.predict(X)
        self.assertTrue(np.array_equal(predictions, y.astype(np.int32)))


if __name__ == "__main__":
    unittest.main()
