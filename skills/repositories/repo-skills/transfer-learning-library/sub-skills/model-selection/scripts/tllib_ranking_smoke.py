#!/usr/bin/env python3
"""CPU smoke test for TLLib ranking metrics.

This script is self-contained and imports the installed ``tllib`` package. It
creates small synthetic NumPy arrays, computes H-score, regularized H-score,
LEEP, NCE, LogME, and TransRate, then asserts that every score is a finite
scalar. It does not download data, load pretrained models, or read source
checkout files.
"""

import argparse
import json
import math
import sys
from typing import Dict

import numpy as np


def _softmax(logits: np.ndarray) -> np.ndarray:
    logits = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(logits)
    return exp / exp.sum(axis=1, keepdims=True)


def make_fixture():
    """Return deterministic features, source probabilities, and target labels."""
    labels = np.repeat(np.arange(3, dtype=np.int64), 6)
    prototypes = np.array(
        [
            [2.0, 0.0, 0.2, 0.0, 1.0],
            [0.0, 2.0, 0.1, 1.0, 0.0],
            [0.2, 0.1, 2.0, 0.0, 0.5],
        ],
        dtype=np.float64,
    )
    offsets = np.array(
        [
            [-0.18, 0.02, 0.03, 0.00, 0.04],
            [-0.10, 0.04, -0.02, 0.05, -0.01],
            [-0.03, -0.04, 0.01, -0.02, 0.03],
            [0.04, 0.03, -0.04, 0.01, -0.03],
            [0.11, -0.02, 0.05, -0.04, 0.02],
            [0.18, -0.03, -0.03, 0.02, -0.04],
        ],
        dtype=np.float64,
    )
    features = np.vstack([prototypes[label] + offsets for label in range(3)])

    # Four source classes with all columns used and positive probability mass.
    source_hint = np.array(
        [0, 0, 3, 0, 3, 0, 1, 1, 2, 1, 2, 1, 2, 2, 3, 2, 3, 2],
        dtype=np.int64,
    )
    logits = np.full((labels.size, 4), -2.0, dtype=np.float64)
    logits[np.arange(labels.size), source_hint] = 2.4
    logits[:, 3] += 0.15 * (labels == 2)
    predictions = _softmax(logits)
    return features, predictions, labels


def compute_scores(features: np.ndarray, predictions: np.ndarray, labels: np.ndarray) -> Dict[str, float]:
    try:
        from tllib.ranking import (
            h_score,
            log_expected_empirical_prediction,
            log_maximum_evidence,
            negative_conditional_entropy,
        )
        from tllib.ranking.hscore import regularized_h_score
        from tllib.ranking.transrate import transrate
    except Exception as exc:  # pragma: no cover - message is for CLI users
        raise RuntimeError(
            "Failed to import TLLib ranking APIs. Install the tllib package and its "
            "NumPy/scikit-learn/numba dependencies before running this smoke."
        ) from exc

    scores = {
        "h_score": h_score(features, labels),
        "regularized_h_score": regularized_h_score(features, labels),
        "logme": log_maximum_evidence(features, labels),
        "transrate": transrate(features, labels),
        "leep": log_expected_empirical_prediction(predictions, labels),
        "nce": negative_conditional_entropy(predictions.argmax(axis=1), labels),
    }
    return {name: float(value) for name, value in scores.items()}


def validate_scores(scores: Dict[str, float]) -> None:
    bad = {name: value for name, value in scores.items() if not math.isfinite(value)}
    if bad:
        raise AssertionError(f"Non-finite ranking scores: {bad}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run a tiny CPU TLLib ranking metric smoke test.")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON only")
    args = parser.parse_args(argv)

    features, predictions, labels = make_fixture()
    assert features.shape == (18, 5)
    assert predictions.shape == (18, 4)
    assert labels.shape == (18,)
    assert np.allclose(predictions.sum(axis=1), 1.0)

    scores = compute_scores(features, predictions, labels)
    validate_scores(scores)

    payload = {
        "status": "ok",
        "num_samples": int(labels.size),
        "feature_dim": int(features.shape[1]),
        "num_target_classes": int(labels.max() + 1),
        "num_source_classes": int(predictions.shape[1]),
        "scores": scores,
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print("TLLib ranking smoke: ok")
        for name in sorted(scores):
            print(f"  {name}: {scores[name]:.6f}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - message is for CLI users
        print(f"TLLib ranking smoke: failed: {exc}", file=sys.stderr)
        raise
