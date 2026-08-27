#!/usr/bin/env python3
"""Tiny CPU smoke for AnchorImage with a custom segmentation function.

Uses a 4x4 single-channel image and a simple deterministic predictor.
"""
from __future__ import annotations

import numpy as np

from alibi.explainers import AnchorImage


def segmentation_fn(image: np.ndarray) -> np.ndarray:
    segments = np.zeros(image.shape[:2], dtype=int)
    half_r = image.shape[0] // 2
    half_c = image.shape[1] // 2
    segments[:half_r, :half_c] = 0
    segments[:half_r, half_c:] = 1
    segments[half_r:, :half_c] = 2
    segments[half_r:, half_c:] = 3
    return segments


def predictor(x: np.ndarray) -> np.ndarray:
    batch = np.asarray(x, dtype=float)
    scores = batch.mean(axis=(1, 2, 3))
    probs = np.stack([1.0 - scores, scores], axis=1)
    probs = np.clip(probs, 1e-6, 1.0)
    probs /= probs.sum(axis=1, keepdims=True)
    return probs


def main() -> int:
    image = np.linspace(0.0, 1.0, 16, dtype=float).reshape(4, 4, 1)
    explainer = AnchorImage(predictor=predictor, image_shape=(4, 4, 1), segmentation_fn=segmentation_fn)
    exp = explainer.explain(image, threshold=0.95)

    print('alibi anchor image smoke: ok')
    print('anchor:', getattr(exp, 'anchor', []))
    print('precision:', getattr(exp, 'precision', None))
    print('coverage:', getattr(exp, 'coverage', None))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
