#!/usr/bin/env python3
"""Run a tiny pomegranate KMeans smoke check."""

from __future__ import annotations

import torch

from pomegranate.kmeans import KMeans


def main() -> int:
    X = torch.tensor(
        [[0.0, 0.0], [0.0, 1.0], [5.0, 5.0], [5.0, 6.0]],
        dtype=torch.float32,
    )
    model = KMeans(k=2, init="first-k", max_iter=10, tol=1e-4)
    labels = model.fit_predict(X)
    centroids = model.centroids
    assert labels.shape == (4,)
    assert centroids.shape == (2, 2)
    print("KMeans smoke passed")
    print("labels:", labels.detach().cpu().tolist())
    print("centroids:", centroids.detach().cpu().round(decimals=4).tolist())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
