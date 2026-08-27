#!/usr/bin/env python3
"""Tiny Darts anomaly scorer/detector smoke on generated data."""
from __future__ import annotations

import argparse
import json

import numpy as np
from darts import TimeSeries
from darts.ad import KMeansScorer, QuantileDetector


def run() -> dict:
    rng = np.random.default_rng(42)
    train_values = 10.0 + 0.1 * rng.normal(size=40)
    val_values = 10.0 + 0.1 * rng.normal(size=40)
    val_values[25] += 4.0
    train = TimeSeries.from_values(train_values)
    val = TimeSeries.from_values(val_values)

    window = 3
    scorer = KMeansScorer(k=2, window=window)
    scorer.fit(train)
    train_scores = scorer.score(train)
    val_scores = scorer.score(val)
    assert len(val_scores) == len(val) - window + 1

    detector = QuantileDetector(high_quantile=0.95)
    detector.fit(train_scores)
    binary = detector.detect(val_scores)
    values = set(float(x) for x in binary.values().flatten())
    assert values.issubset({0.0, 1.0}), values
    assert binary.n_components == val_scores.n_components

    return {
        "status": "ok",
        "window": window,
        "input_length": len(val),
        "score_length": len(val_scores),
        "binary_values": sorted(values),
        "detected_count": float(binary.values().sum()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON result")
    args = parser.parse_args()
    result = run()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Darts anomaly smoke: ok")
        print(result)


if __name__ == "__main__":
    main()
