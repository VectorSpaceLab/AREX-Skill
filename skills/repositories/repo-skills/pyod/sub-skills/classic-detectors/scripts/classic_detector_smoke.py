#!/usr/bin/env python3
"""Run a safe synthetic-data smoke check for PyOD classic detectors.

This helper creates a tiny deterministic numeric dataset, fits one classic PyOD
base detector, scores held-out samples, and reports shape/metric evidence. It
performs no network access, no downloads, and no writes except stdout.

Examples:
    python classic_detector_smoke.py --detector IForest --json
    python classic_detector_smoke.py --detector KNN --n-train 120 --n-test 40
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import numpy as np

DETECTORS = {
    "IForest": ("pyod.models.iforest", "IForest"),
    "KNN": ("pyod.models.knn", "KNN"),
    "ECOD": ("pyod.models.ecod", "ECOD"),
    "COPOD": ("pyod.models.copod", "COPOD"),
    "HBOS": ("pyod.models.hbos", "HBOS"),
}


def _load_detector(name: str):
    import importlib

    module_name, class_name = DETECTORS[name]
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def run(args: argparse.Namespace) -> dict[str, Any]:
    from sklearn.metrics import roc_auc_score
    from pyod.utils.data import generate_data
    from pyod.utils.utility import precision_n_scores

    if not 0.0 < args.contamination <= 0.5:
        raise ValueError("--contamination must be in (0, 0.5]")

    X_train, X_test, y_train, y_test = generate_data(
        n_train=args.n_train,
        n_test=args.n_test,
        n_features=args.n_features,
        contamination=args.contamination,
        random_state=args.random_state,
    )

    Detector = _load_detector(args.detector)
    kwargs: dict[str, Any] = {"contamination": args.contamination}
    if args.detector == "IForest":
        kwargs["random_state"] = args.random_state
    clf = Detector(**kwargs)
    clf.fit(X_train)
    scores = clf.decision_function(X_test)
    labels = clf.predict(X_test)

    return {
        "detector": args.detector,
        "n_train": int(X_train.shape[0]),
        "n_test": int(X_test.shape[0]),
        "n_features": int(X_train.shape[1]),
        "train_score_shape": list(clf.decision_scores_.shape),
        "test_score_shape": list(scores.shape),
        "test_label_shape": list(labels.shape),
        "train_labels_sum": int(np.sum(clf.labels_)),
        "test_labels_sum": int(np.sum(labels)),
        "threshold": float(getattr(clf, "threshold_")),
        "roc_auc": float(roc_auc_score(y_test, scores)),
        "precision_at_n": float(precision_n_scores(y_test, scores)),
        "score_min": float(np.min(scores)),
        "score_max": float(np.max(scores)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--detector", choices=sorted(DETECTORS), default="IForest")
    parser.add_argument("--n-train", type=int, default=120)
    parser.add_argument("--n-test", type=int, default=60)
    parser.add_argument("--n-features", type=int, default=4)
    parser.add_argument("--contamination", type=float, default=0.1)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args(argv)

    try:
        result = run(args)
    except Exception as exc:  # keep helper user-friendly
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Detector: {result['detector']}")
        print(f"Train/test: {result['n_train']}/{result['n_test']} x {result['n_features']}")
        print(f"Threshold: {result['threshold']:.6g}")
        print(f"Flagged train/test: {result['train_labels_sum']}/{result['test_labels_sum']}")
        print(f"ROC-AUC: {result['roc_auc']:.4f}")
        print(f"Precision @ n: {result['precision_at_n']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
