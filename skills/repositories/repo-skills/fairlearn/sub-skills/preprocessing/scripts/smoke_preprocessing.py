#!/usr/bin/env python3
"""Tiny Fairlearn preprocessing smoke check."""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from fairlearn.preprocessing import CorrelationRemover, PrototypeRepresentationLearner


def run_correlation_remover() -> None:
    X = pd.DataFrame(
        {
            "score": [0.1, 0.2, 0.8, 0.9, 0.35, 0.65, 0.75, 0.15],
            "proxy": [1.0, 1.1, 2.1, 2.2, 1.4, 1.9, 2.0, 1.2],
            "group_code": [0, 0, 1, 1, 0, 1, 1, 0],
        }
    )
    remover = CorrelationRemover(sensitive_feature_ids=["group_code"], alpha=1.0)
    transformed = remover.fit_transform(X)
    print("CorrelationRemover output shape:", transformed.shape)
    if transformed.shape != (len(X), 2):
        raise AssertionError("CorrelationRemover should return two non-sensitive transformed columns")


def run_prototype_representation_learner(max_iter: int) -> None:
    X = np.array(
        [
            [0.0, 0.1],
            [0.2, 0.0],
            [0.8, 0.7],
            [0.9, 0.8],
            [0.3, 0.4],
            [0.7, 0.6],
            [0.6, 0.9],
            [0.1, 0.2],
        ],
        dtype=float,
    )
    y = np.array([0, 0, 1, 1, 0, 1, 1, 0])
    sensitive = np.array([0, 0, 1, 1, 0, 1, 1, 0])
    learner = PrototypeRepresentationLearner(n_prototypes=2, max_iter=max_iter, random_state=0)
    transformed = learner.fit_transform(X, y, sensitive_features=sensitive)
    print("PrototypeRepresentationLearner output shape:", transformed.shape)
    if transformed.shape[0] != X.shape[0]:
        raise AssertionError("PrototypeRepresentationLearner must preserve sample count")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-iter", type=int, default=25, help="Max iterations for PrototypeRepresentationLearner smoke.")
    args = parser.parse_args()
    run_correlation_remover()
    run_prototype_representation_learner(args.max_iter)
    print("Preprocessing smoke check completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
