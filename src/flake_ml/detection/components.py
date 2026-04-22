from __future__ import annotations

from collections import deque

import numpy as np


def _neighbors(mask: np.ndarray) -> list[np.ndarray]:
    padded = np.pad(mask, 1, mode="constant", constant_values=False)
    height, width = mask.shape
    return [padded[row:row + height, col:col + width] for row in range(3) for col in range(3)]


def binary_dilate(mask: np.ndarray) -> np.ndarray:
    return np.logical_or.reduce(_neighbors(mask))


def binary_erode(mask: np.ndarray) -> np.ndarray:
    return np.logical_and.reduce(_neighbors(mask))


def binary_open(mask: np.ndarray, iterations: int = 1) -> np.ndarray:
    result = mask.astype(bool)
    for _ in range(iterations):
        result = binary_erode(result)
    for _ in range(iterations):
        result = binary_dilate(result)
    return result


def binary_close(mask: np.ndarray, iterations: int = 1) -> np.ndarray:
    result = mask.astype(bool)
    for _ in range(iterations):
        result = binary_dilate(result)
    for _ in range(iterations):
        result = binary_erode(result)
    return result


def connected_components(mask: np.ndarray) -> list[np.ndarray]:
    mask = mask.astype(bool)
    height, width = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    components: list[np.ndarray] = []

    for row in range(height):
        for col in range(width):
            if not mask[row, col] or visited[row, col]:
                continue

            queue: deque[tuple[int, int]] = deque([(row, col)])
            visited[row, col] = True
            pixels: list[tuple[int, int]] = []

            while queue:
                current_row, current_col = queue.popleft()
                pixels.append((current_row, current_col))

                for d_row in (-1, 0, 1):
                    for d_col in (-1, 0, 1):
                        if d_row == 0 and d_col == 0:
                            continue
                        next_row = current_row + d_row
                        next_col = current_col + d_col
                        if not (0 <= next_row < height and 0 <= next_col < width):
                            continue
                        if visited[next_row, next_col] or not mask[next_row, next_col]:
                            continue
                        visited[next_row, next_col] = True
                        queue.append((next_row, next_col))

            component = np.zeros_like(mask, dtype=bool)
            for pixel_row, pixel_col in pixels:
                component[pixel_row, pixel_col] = True
            components.append(component)

    return components

