#!/usr/bin/env python3
"""Deterministic CPU-only smoke checks for PyOD core time-series detectors."""
from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any, Dict, Iterable, List

import numpy as np


CORE_DETECTORS = ["time-series-od", "spectral-residual", "matrix-profile", "kshape", "sand"]


def generate_data(args: argparse.Namespace):
    from pyod.utils.data import generate_ts_data

    return generate_ts_data(
        n_train=args.n_train,
        n_test=args.n_test,
        n_channels=args.n_channels,
        contamination=args.synthetic_contamination,
        anomaly_type=args.anomaly_type,
        random_state=args.random_state,
    )


def finite_summary(values: np.ndarray) -> Dict[str, Any]:
    arr = np.asarray(values, dtype=float)
    return {
        "shape": list(arr.shape),
        "finite": bool(np.isfinite(arr).all()),
        "min": float(np.nanmin(arr)),
        "max": float(np.nanmax(arr)),
        "mean": float(np.nanmean(arr)),
    }


def build_detector(name: str, args: argparse.Namespace):
    if name == "time-series-od":
        from pyod.models.ts_od import TimeSeriesOD

        return TimeSeriesOD(
            detector=args.inner_detector,
            window_size=args.window_size,
            step=args.step,
            score_aggregation=args.score_aggregation,
            contamination=args.contamination,
        )
    if name == "spectral-residual":
        from pyod.models.ts_spectral_residual import SpectralResidual

        return SpectralResidual(
            score_window=args.score_window,
            channel_aggregation=args.channel_aggregation,
            contamination=args.contamination,
        )
    if name == "matrix-profile":
        from pyod.models.ts_matrix_profile import MatrixProfile

        return MatrixProfile(
            window_size=args.window_size,
            channel_aggregation=args.channel_aggregation,
            contamination=args.contamination,
        )
    if name == "kshape":
        from pyod.models.ts_kshape import KShape

        return KShape(
            n_clusters=args.n_clusters,
            window_size=args.window_size,
            max_iter=args.max_iter,
            channel_aggregation=args.channel_aggregation,
            random_state=args.random_state,
            contamination=args.contamination,
        )
    if name == "sand":
        from pyod.models.ts_sand import SAND

        return SAND(
            n_clusters=args.n_clusters,
            window_size=args.window_size,
            batch_size=args.sand_batch_size,
            max_iter=args.max_iter,
            alpha=args.sand_alpha,
            channel_aggregation=args.channel_aggregation,
            random_state=args.random_state,
            contamination=args.contamination,
        )
    raise ValueError(f"unknown detector: {name}")


def run_one(name: str, X_train: np.ndarray, X_test: np.ndarray, args: argparse.Namespace) -> Dict[str, Any]:
    started = time.perf_counter()
    clf = build_detector(name, args)
    clf.fit(X_train)
    elapsed = time.perf_counter() - started
    result: Dict[str, Any] = {
        "detector": name,
        "class": clf.__class__.__name__,
        "fit_seconds": round(elapsed, 6),
        "train_scores": finite_summary(clf.decision_scores_),
        "labels_shape": list(np.asarray(clf.labels_).shape),
        "threshold": float(clf.threshold_),
        "ok": True,
    }

    if name == "matrix-profile":
        try:
            clf.decision_function(X_test)
        except NotImplementedError as exc:
            result["transductive_verified"] = True
            result["decision_function_error"] = str(exc)
        else:
            result["ok"] = False
            result["transductive_verified"] = False
            result["error"] = "MatrixProfile decision_function unexpectedly succeeded"
        return result

    scores = clf.decision_function(X_test)
    result["test_scores"] = finite_summary(scores)
    labels = clf.predict(X_test)
    result["test_labels_shape"] = list(np.asarray(labels).shape)
    result["test_labels_unique"] = sorted(int(x) for x in set(np.asarray(labels).ravel().tolist()))
    return result


def selected_detectors(value: str) -> Iterable[str]:
    if value == "all":
        return CORE_DETECTORS
    return [value]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run deterministic CPU-only PyOD core time-series smoke checks on synthetic data."
    )
    parser.add_argument("--detector", choices=["all"] + CORE_DETECTORS, default="all")
    parser.add_argument("--n-train", type=int, default=160)
    parser.add_argument("--n-test", type=int, default=64)
    parser.add_argument("--n-channels", type=int, default=1)
    parser.add_argument("--window-size", type=int, default=12)
    parser.add_argument("--step", type=int, default=1)
    parser.add_argument("--inner-detector", default="ECOD", help="Inner detector for TimeSeriesOD. Default: ECOD.")
    parser.add_argument("--score-aggregation", choices=["max", "mean"], default="max")
    parser.add_argument("--channel-aggregation", choices=["max", "mean"], default="max")
    parser.add_argument("--score-window", type=int, default=3)
    parser.add_argument("--n-clusters", type=int, default=2)
    parser.add_argument("--max-iter", type=int, default=5)
    parser.add_argument("--sand-batch-size", type=int, default=32)
    parser.add_argument("--sand-alpha", type=float, default=0.5)
    parser.add_argument("--contamination", type=float, default=0.1)
    parser.add_argument("--synthetic-contamination", type=float, default=0.05)
    parser.add_argument("--anomaly-type", choices=["point", "subsequence", "both"], default="both")
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--json", action="store_true", help="Emit JSON only. Default is JSON followed by no prose, kept for stable parsing.")
    parser.add_argument("--keep-going", action="store_true", help="Continue after detector failures and report them all.")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.n_train < 20 or args.n_test < 20:
        raise ValueError("n-train and n-test must each be at least 20")
    if args.n_channels < 1:
        raise ValueError("n-channels must be at least 1")
    if args.window_size < 2:
        raise ValueError("window-size must be at least 2")
    if args.n_train < args.window_size + 1:
        raise ValueError("n-train must be greater than window-size for all default detectors")
    n_windows = args.n_train - args.window_size + 1
    if n_windows < args.n_clusters:
        raise ValueError("n-clusters cannot exceed the number of training windows")
    if min(args.contamination, args.synthetic_contamination) <= 0 or max(args.contamination, args.synthetic_contamination) >= 0.5:
        raise ValueError("contamination values must be in (0, 0.5)")


def main() -> int:
    args = parse_args()
    try:
        validate_args(args)
        X_train, X_test, y_train, y_test = generate_data(args)
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "stage": "setup", "error": f"{exc.__class__.__name__}: {exc}"}, indent=2), file=sys.stderr)
        return 2

    report: Dict[str, Any] = {
        "ok": True,
        "cpu_only": True,
        "data": {
            "train_shape": list(np.asarray(X_train).shape),
            "test_shape": list(np.asarray(X_test).shape),
            "y_train_anomalies": int(np.asarray(y_train).sum()),
            "y_test_anomalies": int(np.asarray(y_test).sum()),
        },
        "detectors": [],
    }

    for name in selected_detectors(args.detector):
        try:
            result = run_one(name, X_train, X_test, args)
        except Exception as exc:  # noqa: BLE001
            result = {"detector": name, "ok": False, "error": f"{exc.__class__.__name__}: {exc}"}
            report["ok"] = False
            report["detectors"].append(result)
            if not args.keep_going:
                print(json.dumps(report, indent=2, sort_keys=True))
                return 1
        else:
            if not result.get("ok", False):
                report["ok"] = False
            report["detectors"].append(result)

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
