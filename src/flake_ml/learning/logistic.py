from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class LogisticRegressor:
    learning_rate: float = 0.1
    epochs: int = 500
    l2: float = 1e-3

    weights_: np.ndarray | None = None
    bias_: float = 0.0
    mean_: np.ndarray | None = None
    std_: np.ndarray | None = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LogisticRegressor":
        X = np.asarray(X, dtype=np.float32)
        y = np.asarray(y, dtype=np.float32).reshape(-1)
        if X.ndim != 2:
            raise ValueError("X must be 2D.")
        if y.shape[0] != X.shape[0]:
            raise ValueError("X and y must have the same number of rows.")

        self.mean_ = X.mean(axis=0)
        self.std_ = np.where(X.std(axis=0) < 1e-6, 1.0, X.std(axis=0))
        Xn = (X - self.mean_) / self.std_

        self.weights_ = np.zeros(X.shape[1], dtype=np.float32)
        self.bias_ = 0.0

        for _ in range(self.epochs):
            logits = Xn @ self.weights_ + self.bias_
            predictions = 1.0 / (1.0 + np.exp(-logits))
            error = predictions - y
            grad_w = (Xn.T @ error) / Xn.shape[0] + self.l2 * self.weights_
            grad_b = float(np.mean(error))
            self.weights_ -= self.learning_rate * grad_w
            self.bias_ -= self.learning_rate * grad_b
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        self._check_fitted()
        X = np.asarray(X, dtype=np.float32)
        Xn = (X - self.mean_) / self.std_
        logits = Xn @ self.weights_ + self.bias_
        probabilities = 1.0 / (1.0 + np.exp(-logits))
        return np.stack([1.0 - probabilities, probabilities], axis=1)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(np.int32)

    def _check_fitted(self) -> None:
        if self.weights_ is None or self.mean_ is None or self.std_ is None:
            raise RuntimeError("Model is not fitted.")

