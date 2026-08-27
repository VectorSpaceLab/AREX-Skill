#!/usr/bin/env python3
"""Run a tiny deterministic pmdarima temporal-CV smoke check.

This script is deliberately local and bounded: it creates 24 in-memory rows,
uses a fixed low-order ARIMA with maxiter=10, performs no network access or
plotting, and writes no files.  It checks positional X alignment, holdout and
fold geometry, raw error scoring, timing results, and cross-validated forecast
shapes.  Invoke it by path from any working directory.
"""

from __future__ import annotations

import argparse
import sys
import warnings

import numpy as np

N_SAMPLES = 24
MAX_FOLDS = N_SAMPLES - 1


def make_data(n_samples: int = N_SAMPLES) -> tuple[np.ndarray, np.ndarray]:
    """Return deterministic positive targets and known toy exogenous rows."""
    t = np.arange(n_samples, dtype=float)
    y = 10.0 + 0.20 * t + 0.25 * np.sin(t / 2.0)
    X = np.column_stack((np.sin(t / 3.0), np.cos(t / 4.0)))
    return y, X


def custom_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """A callable scorer with pmdarima's (true, predicted) contract."""
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))


def expect_value_error(action, label: str) -> None:
    try:
        action()
    except ValueError:
        return
    raise AssertionError(f"{label} did not raise ValueError")


def assert_split_safety(cv, y: np.ndarray, X: np.ndarray):
    """Materialize and assert chronology, horizon, disjointness, and X rows."""
    folds = list(cv.split(y, X))
    assert folds, "the chosen geometry produced no usable folds"
    assert len(folds) <= MAX_FOLDS, (len(folds), MAX_FOLDS)
    for train_idx, test_idx in folds:
        assert len(test_idx) == cv.horizon
        assert train_idx[-1] < test_idx[0], (train_idx, test_idx)
        assert np.intersect1d(train_idx, test_idx).size == 0
        assert np.isfinite(X[train_idx]).all()
        assert np.isfinite(X[test_idx]).all()

    expect_value_error(
        lambda: list(cv.split(y, X[:-1])),
        "an exogenous matrix shorter than y",
    )
    missing_future_X = X.copy()
    missing_future_X[folds[0][1], :] = np.nan
    expect_value_error(
        lambda: assert_finite_test_rows(missing_future_X, folds),
        "missing future exogenous data",
    )
    return folds


def assert_finite_test_rows(X: np.ndarray, folds) -> None:
    test_positions = np.concatenate([test_idx for _, test_idx in folds])
    if not np.isfinite(X[test_positions]).all():
        raise ValueError("future exogenous rows are absent or non-finite")


def make_cv(args: argparse.Namespace):
    if args.cv == "rolling":
        return RollingForecastCV(h=args.h, step=args.step, initial=args.initial)
    return SlidingWindowForecastCV(
        h=args.h, step=args.step, window_size=args.window_size
    )


def run_geometry_checks(y: np.ndarray) -> None:
    """Exercise invalid geometry and no-fold short-series behavior."""
    expect_value_error(
        lambda: RollingForecastCV(h=0), "non-positive forecasting horizon"
    )
    expect_value_error(
        lambda: list(RollingForecastCV(h=2, initial=5).split(y[:6])),
        "rolling initial+h beyond a short series",
    )
    expect_value_error(
        lambda: list(SlidingWindowForecastCV(h=2, window_size=2).split(y)),
        "sliding window below the minimum size",
    )
    expect_value_error(
        lambda: list(SlidingWindowForecastCV(h=3, window_size=22).split(y)),
        "sliding window+h beyond the series",
    )
    assert list(RollingForecastCV(h=2).split(y[:1])) == []
    assert list(SlidingWindowForecastCV(h=2).split(y[:1])) == []


def build_estimator(pm):
    # Model fitting is intentionally not the subject of this route.
    return pm.ARIMA(
        order=(0, 0, 0),
        with_intercept=False,
        maxiter=10,
        suppress_warnings=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run deterministic rolling/sliding pmdarima forecast CV and "
            "assert fold, score, timing, and prediction shapes."
        )
    )
    parser.add_argument(
        "--cv",
        choices=("rolling", "sliding"),
        default="rolling",
        help="temporal splitter (default: rolling)",
    )
    parser.add_argument("--h", type=int, default=2, help="forecast horizon")
    parser.add_argument("--step", type=int, default=1, help="origin step")
    parser.add_argument(
        "--initial", type=int, default=10,
        help="rolling initial training length (default: 10)",
    )
    parser.add_argument(
        "--window-size", type=int, default=8,
        help="sliding training window length (default: 8)",
    )
    parser.add_argument(
        "--scoring",
        choices=("smape", "mean_absolute_error", "mean_squared_error", "custom-mae"),
        default="smape",
        help="raw error metric; lower is better (default: smape)",
    )
    parser.add_argument(
        "--raw-predictions", action="store_true",
        help="assert the sparse (n_samples, h) prediction matrix",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.step > args.h:
        print(
            "invalid prediction geometry: --step must be <= --h for "
            "cross_val_predict",
            file=sys.stderr,
        )
        return 2

    try:
        import pmdarima as pm
        from pmdarima.model_selection import (
            RollingForecastCV as _RollingForecastCV,
            SlidingWindowForecastCV as _SlidingWindowForecastCV,
            cross_val_predict as _cross_val_predict,
            cross_val_score as _cross_val_score,
            cross_validate as _cross_validate,
            train_test_split as _train_test_split,
        )
        globals().update(
            {
                "RollingForecastCV": _RollingForecastCV,
                "SlidingWindowForecastCV": _SlidingWindowForecastCV,
            }
        )
        cross_val_predict = _cross_val_predict
        cross_val_score = _cross_val_score
        cross_validate = _cross_validate
        train_test_split = _train_test_split
    except ImportError as exc:
        print(f"pmdarima is required for the smoke run: {exc}", file=sys.stderr)
        return 2

    # One positional split proves that y and X receive the same boundary.
    y, X = make_data()
    run_geometry_checks(y)

    # One positional split proves that y and X receive the same boundary.
    y_train, y_final, X_train, X_final = train_test_split(y, X, test_size=4)
    assert len(y_train) == X_train.shape[0] == 20
    assert len(y_final) == X_final.shape[0] == 4
    assert np.array_equal(np.concatenate((y_train, y_final)), y)

    cv = make_cv(args)
    try:
        folds = assert_split_safety(cv, y_train, X_train)
    except ValueError as exc:
        print(f"invalid validation geometry: {exc}", file=sys.stderr)
        return 2

    scorer = custom_mae if args.scoring == "custom-mae" else args.scoring
    estimator = build_estimator(pm)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        scores = cross_val_score(
            estimator, y_train, X=X_train, scoring=scorer, cv=cv,
            error_score="raise",
        )
        timed = cross_validate(
            estimator, y_train, X=X_train, scoring=scorer, cv=cv,
            error_score="raise",
        )
        predictions = cross_val_predict(
            estimator, y_train, X=X_train, cv=cv,
            averaging="mean", return_raw_predictions=args.raw_predictions,
        )

    assert scores.shape == (len(folds),), (scores.shape, len(folds))
    assert np.array_equal(scores, timed["test_score"])
    assert timed["fit_time"].shape == timed["score_time"].shape == scores.shape
    assert np.isfinite(scores).all(), scores

    if args.raw_predictions:
        expected_shape = (len(y_train), cv.horizon)
    else:
        covered = np.unique(np.concatenate([test_idx for _, test_idx in folds]))
        expected_shape = (len(covered),)
    assert predictions.shape == expected_shape, (predictions.shape, expected_shape)

    print(f"cv={args.cv} folds={len(folds)} h={cv.horizon} step={cv.step}")
    print(f"scores_shape={scores.shape} prediction_shape={predictions.shape}")
    print(f"best_fold={int(np.argmin(scores))} lowest_error={float(np.min(scores)):.6f}")
    print("checks=holdout, chronology, X alignment, geometry guards, scoring, timing, prediction shape")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
