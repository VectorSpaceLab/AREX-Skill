#!/usr/bin/env python3
"""Tiny smoke helper for direct single-GPU cuML estimators.

The helper runs a few small GPU-backed workflows and can optionally verify a
trusted local pickle round-trip. It stays self-contained and only imports the
installed cuML package at runtime.
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
import tempfile
from pathlib import Path

import numpy as np

CASE_ORDER = ("kmeans", "linear-regression", "random-forest")
CASE_CHOICES = (*CASE_ORDER, "all")

_BACKEND_HINTS = (
    "no module named 'cuml'",
    "no module named 'libcuml'",
    "no module named 'cupy'",
    "libcuml",
    "cudaruntimeerror",
    "cudaerror",
    "cuda driver",
    "cupy_backends",
    "rmm",
)


class BackendUnavailableError(RuntimeError):
    """Raised when cuML or its CUDA backend is not available."""


def _is_backend_issue(exc: Exception) -> bool:
    message = f"{exc.__class__.__name__}: {exc}".lower()
    return any(hint in message for hint in _BACKEND_HINTS)


def _as_numpy(value):
    if isinstance(value, np.ndarray):
        return value

    try:
        import cupy as cp
    except Exception:
        cp = None

    if cp is not None and isinstance(value, cp.ndarray):
        return cp.asnumpy(value)

    if hasattr(value, "to_numpy"):
        return value.to_numpy()

    return np.asarray(value)


def _assert_same(name: str, expected, observed) -> None:
    expected_np = _as_numpy(expected)
    observed_np = _as_numpy(observed)

    if expected_np.shape != observed_np.shape:
        raise AssertionError(
            f"{name} shape mismatch: {expected_np.shape} != {observed_np.shape}"
        )

    if np.issubdtype(expected_np.dtype, np.floating) or np.issubdtype(
        observed_np.dtype, np.floating
    ):
        np.testing.assert_allclose(
            observed_np,
            expected_np,
            rtol=1e-6,
            atol=1e-7,
            err_msg=name,
        )
    else:
        np.testing.assert_array_equal(observed_np, expected_np, err_msg=name)


def _pickle_round_trip(model, X, predict_fn) -> bool:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "model.pkl"
        with path.open("wb") as fh:
            pickle.dump(model, fh, protocol=5)
        with path.open("rb") as fh:
            restored = pickle.load(fh)

        baseline = predict_fn(model, X)
        recovered = predict_fn(restored, X)
        _assert_same("pickle round-trip", baseline, recovered)

    return True


def _run_kmeans(check_pickle: bool) -> dict[str, object]:
    try:
        import cuml
        from cuml.cluster import KMeans
        from cuml.datasets import make_blobs
        from cuml.metrics import adjusted_rand_score

        with cuml.using_output_type("numpy"):
            X, y = make_blobs(
                n_samples=96,
                n_features=6,
                centers=3,
                cluster_std=0.35,
                random_state=0,
            )
            model = KMeans(n_clusters=3, n_init=2, random_state=0)
            model.fit(X)
            labels = model.predict(X)
            ari = float(adjusted_rand_score(y, labels))

            if not np.isfinite(ari):
                raise AssertionError("kmeans ARI is not finite")

            result: dict[str, object] = {"ari": ari}
            if check_pickle:
                _pickle_round_trip(model, X, lambda fitted, data: fitted.predict(data))
                result["pickle_round_trip"] = True
            return result
    except Exception as exc:
        if _is_backend_issue(exc):
            raise BackendUnavailableError(str(exc)) from exc
        raise


def _run_linear_regression(check_pickle: bool) -> dict[str, object]:
    try:
        import cuml
        from cuml import LinearRegression
        from cuml.datasets import make_regression
        from cuml.model_selection import train_test_split

        with cuml.using_output_type("numpy"):
            X, y = make_regression(
                n_samples=128,
                n_features=12,
                n_informative=8,
                random_state=0,
            )
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, random_state=0
            )
            model = LinearRegression()
            model.fit(X_train, y_train)
            r2 = float(model.score(X_test, y_test))

            if not np.isfinite(r2):
                raise AssertionError("linear regression score is not finite")

            result: dict[str, object] = {"r2": r2}
            if check_pickle:
                _pickle_round_trip(model, X_test, lambda fitted, data: fitted.predict(data))
                result["pickle_round_trip"] = True
            return result
    except Exception as exc:
        if _is_backend_issue(exc):
            raise BackendUnavailableError(str(exc)) from exc
        raise


def _run_random_forest(check_pickle: bool) -> dict[str, object]:
    try:
        import cuml
        from cuml.ensemble import RandomForestClassifier
        from cuml.datasets import make_classification
        from cuml.model_selection import train_test_split

        with cuml.using_output_type("numpy"):
            X, y = make_classification(
                n_samples=160,
                n_features=12,
                n_informative=8,
                n_redundant=0,
                n_classes=2,
                n_clusters_per_class=1,
                class_sep=1.5,
                random_state=0,
            )
            X = X.astype(np.float32)
            y = y.astype(np.int32)
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, random_state=0
            )
            model = RandomForestClassifier(
                n_estimators=10,
                max_depth=4,
                n_bins=32,
                random_state=0,
            )
            model.fit(X_train, y_train)
            accuracy = float(model.score(X_test, y_test))

            if not np.isfinite(accuracy):
                raise AssertionError("random forest score is not finite")

            result: dict[str, object] = {"accuracy": accuracy}
            if check_pickle:
                _pickle_round_trip(model, X_test, lambda fitted, data: fitted.predict(data))
                result["pickle_round_trip"] = True
            return result
    except Exception as exc:
        if _is_backend_issue(exc):
            raise BackendUnavailableError(str(exc)) from exc
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke-test tiny direct cuML estimator workflows."
    )
    parser.add_argument(
        "--case",
        choices=CASE_CHOICES,
        default="all",
        help="Which tiny estimator workflow to run.",
    )
    parser.add_argument(
        "--check-pickle",
        action="store_true",
        help="Also verify a trusted local pickle round-trip.",
    )
    return parser


def run_selected_cases(case: str, check_pickle: bool) -> dict[str, dict[str, object]]:
    runners = {
        "kmeans": _run_kmeans,
        "linear-regression": _run_linear_regression,
        "random-forest": _run_random_forest,
    }
    if case == "all":
        return {name: runners[name](check_pickle) for name in CASE_ORDER}
    return {case: runners[case](check_pickle)}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        results = run_selected_cases(args.case, args.check_pickle)
    except BackendUnavailableError as exc:
        print(f"cuML/CUDA backend unavailable: {exc}", file=sys.stderr)
        return 2

    summary = {"case": args.case, "results": results}
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
