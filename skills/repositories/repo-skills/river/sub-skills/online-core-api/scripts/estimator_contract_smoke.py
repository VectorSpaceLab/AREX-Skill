#!/usr/bin/env python3
"""Run River estimator lifecycle and generic-check smoke tests."""

from __future__ import annotations

import argparse
import math
import sys

from river import anomaly, checks, cluster, drift, dummy, preprocessing, stats, utils


def require(condition: bool, stage: str, message: str) -> None:
    if not condition:
        raise AssertionError(f"{stage}: {message}")


def close(actual: float, expected: float, tol: float = 1e-9) -> bool:
    return math.isclose(float(actual), float(expected), rel_tol=tol, abs_tol=tol)


def run_manual_smoke() -> None:
    x = {"x": 1.0}

    stage = "manual/classifier"
    classifier = dummy.NoChangeClassifier()
    require(classifier.predict_one(x) is None, stage, "fresh classifier should return None")
    require(classifier.predict_proba_one(x) == {}, stage, "fresh classifier should return {}")
    require(classifier.learn_one(x, "spam") is None, stage, "learn_one should return None")
    require(classifier.predict_one(x) == "spam", stage, "classifier should predict the seen label")
    proba = classifier.predict_proba_one(x)
    require(set(proba) == {"spam"}, stage, "classifier should expose the seen label")
    require(close(proba["spam"], 1.0), stage, "classifier probability should be 1.0")
    require(classifier.learn_one(x, "ham") is None, stage, "learn_one should return None")
    proba = classifier.predict_proba_one(x)
    require(set(proba) == {"spam", "ham"}, stage, "classifier should keep both seen labels")
    require(close(proba["ham"], 1.0), stage, "last label should have probability 1.0")

    stage = "manual/regressor"
    regressor = dummy.StatisticRegressor(stats.Mean())
    require(close(regressor.predict_one(x), 0.0), stage, "fresh regressor should emit its default mean")
    require(regressor.learn_one(x, 2.0) is None, stage, "learn_one should return None")
    require(close(regressor.predict_one(x), 2.0), stage, "regressor should track the running mean")
    require(regressor.learn_one(x, 4.0) is None, stage, "learn_one should return None")
    require(close(regressor.predict_one(x), 3.0), stage, "regressor should keep updating the mean")

    stage = "manual/transformer"
    transformer = preprocessing.StandardScaler()
    require(transformer.transform_one(x) == {"x": 0.0}, stage, "fresh scaler should emit zeroed features")
    require(transformer.learn_one(x) is None, stage, "learn_one should return None")
    transformed = transformer.transform_one(x)
    require(isinstance(transformed, dict), stage, "transform_one should return a dict")
    require(set(transformed) == {"x"}, stage, "transform_one should preserve the feature key")

    stage = "manual/clusterer"
    clusterer = cluster.KMeans(n_clusters=2, seed=42)
    cluster_id = clusterer.predict_one({"x": 0.0, "y": 0.0})
    require(isinstance(cluster_id, int), stage, "predict_one should return a cluster id")
    require(clusterer.learn_one({"x": 0.0, "y": 0.0}) is None, stage, "learn_one should return None")
    cluster_id = clusterer.predict_one({"x": 1.0, "y": 1.0})
    require(isinstance(cluster_id, int), stage, "predict_one should keep returning cluster ids")

    stage = "manual/anomaly"
    detector = anomaly.HalfSpaceTrees(seed=42)
    require(close(detector.score_one({"x": 0.1}), 0.0), stage, "fresh detector should return zero score")
    require(detector.learn_one({"x": 0.1}) is None, stage, "learn_one should return None")
    score = detector.score_one({"x": 0.2})
    require(isinstance(score, (int, float)), stage, "score_one should return a numeric score")

    stage = "manual/drift"
    drift_detector = drift.ADWIN()
    require(drift_detector.drift_detected is False, stage, "fresh detector should not report drift")
    require(drift_detector.update(0.0) is None, stage, "update should return None")
    for value in [0.0, 0.0, 1.0, 1.0, 1.0, 1.0]:
        require(drift_detector.update(value) is None, stage, "update should keep returning None")
    require(isinstance(drift_detector.drift_detected, bool), stage, "drift_detected should stay boolean")


def run_check_smoke() -> None:
    cases = [
        ("NoChangeClassifier", dummy.NoChangeClassifier()),
        ("StatisticRegressor", dummy.StatisticRegressor(stats.Mean())),
        ("StandardScaler", preprocessing.StandardScaler()),
        ("KMeans", cluster.KMeans(seed=42)),
    ]

    if not utils.pandas.PANDAS_INSTALLED:
        print("check_estimator: pandas extra unavailable; batch checks may be skipped")

    for name, model in cases:
        print(f"check_estimator: {name} ...")
        checks.check_estimator(model)
        print(f"check_estimator: {name} ok")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a River estimator lifecycle and check smoke.")
    parser.add_argument(
        "--mode",
        choices=("manual", "checks", "all"),
        default="all",
        help="Run only the manual lifecycle, only check_estimator smoke, or both.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.mode in {"manual", "all"}:
            print("manual: start")
            run_manual_smoke()
            print("manual: ok")
        if args.mode in {"checks", "all"}:
            print("checks: start")
            run_check_smoke()
            print("checks: ok")
    except Exception as exc:
        print(f"SMOKE FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("SMOKE OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
