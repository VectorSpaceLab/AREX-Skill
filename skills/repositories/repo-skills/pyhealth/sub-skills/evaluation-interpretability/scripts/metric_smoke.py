#!/usr/bin/env python3
"""Deterministic PyHealth metric smoke on non-clinical arrays."""
import argparse
import json
import numpy as np
from pyhealth.metrics import binary_metrics_fn, multilabel_metrics_fn


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--multilabel", action="store_true")
    args = parser.parse_args()
    if args.multilabel:
        y_true = np.array([[1, 0], [0, 1], [1, 1]])
        y_prob = np.array([[.8, .2], [.1, .9], [.7, .6]])
        out = multilabel_metrics_fn(y_true, y_prob)
    else:
        y_true = np.array([0, 1, 0, 1])
        y_prob = np.array([.1, .8, .2, .7])
        out = binary_metrics_fn(y_true, y_prob, metrics=["accuracy", "roc_auc", "f1"])
    clean = {key: float(value) for key, value in out.items()}
    print(json.dumps(clean, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
