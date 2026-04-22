from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class GaussianMixtureModel:
    n_components: int
    max_iter: int = 100
    tol: float = 1e-4
    seed: int = 7

    weights_: np.ndarray | None = None
    means_: np.ndarray | None = None
    variances_: np.ndarray | None = None

    def fit(self, X: np.ndarray) -> "GaussianMixtureModel":
        X = np.asarray(X, dtype=np.float32)
        if X.ndim != 2:
            raise ValueError("X must be a 2D array.")
        n_samples, n_features = X.shape
        if n_samples < self.n_components:
            raise ValueError("Number of samples must be at least n_components.")

        rng = np.random.default_rng(self.seed)
        chosen = rng.choice(n_samples, size=self.n_components, replace=False)
        means = X[chosen].copy()
        variances = np.tile(np.var(X, axis=0, keepdims=True) + 1e-3, (self.n_components, 1))
        weights = np.full(self.n_components, 1.0 / self.n_components, dtype=np.float32)

        previous_log_likelihood = None
        for _ in range(self.max_iter):
            responsibilities = self._estimate_responsibilities(X, weights, means, variances)
            soft_counts = responsibilities.sum(axis=0) + 1e-8

            weights = soft_counts / n_samples
            means = (responsibilities.T @ X) / soft_counts[:, None]
            for component in range(self.n_components):
                diff = X - means[component]
                variances[component] = np.sum(responsibilities[:, component][:, None] * diff * diff, axis=0) / soft_counts[component]
            variances = np.maximum(variances, 1e-6)

            log_likelihood = float(np.sum(np.log(np.sum(self._component_density(X, weights, means, variances), axis=1) + 1e-12)))
            if previous_log_likelihood is not None and abs(log_likelihood - previous_log_likelihood) < self.tol:
                break
            previous_log_likelihood = log_likelihood

        self.weights_ = weights
        self.means_ = means
        self.variances_ = variances
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        self._check_fitted()
        X = np.asarray(X, dtype=np.float32)
        return self._estimate_responsibilities(X, self.weights_, self.means_, self.variances_)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.argmax(self.predict_proba(X), axis=1)

    def _component_density(
        self,
        X: np.ndarray,
        weights: np.ndarray,
        means: np.ndarray,
        variances: np.ndarray,
    ) -> np.ndarray:
        n_components = means.shape[0]
        densities = np.zeros((X.shape[0], n_components), dtype=np.float32)
        for component in range(n_components):
            diff = X - means[component]
            log_det = np.sum(np.log(2.0 * np.pi * variances[component]))
            mahalanobis = np.sum((diff * diff) / variances[component], axis=1)
            densities[:, component] = weights[component] * np.exp(-0.5 * (log_det + mahalanobis))
        return densities

    def _estimate_responsibilities(
        self,
        X: np.ndarray,
        weights: np.ndarray,
        means: np.ndarray,
        variances: np.ndarray,
    ) -> np.ndarray:
        weighted = self._component_density(X, weights, means, variances)
        normalizer = np.sum(weighted, axis=1, keepdims=True) + 1e-12
        return weighted / normalizer

    def _check_fitted(self) -> None:
        if self.weights_ is None or self.means_ is None or self.variances_ is None:
            raise RuntimeError("Model is not fitted.")

