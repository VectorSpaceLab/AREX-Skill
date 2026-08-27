#!/usr/bin/env python3
"""Deterministic tiny helper for missing-value-imputation masks and scoring.

This script does not import LimiX, load checkpoints, or run model inference. It
adapts the MVI mask/evaluation pattern into a safe standalone fixture: generate
a NaN mask, keep the unmasked original for validation, and compute categorical
error plus continuous RMSE for reconstructed arrays.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class MviMetrics:
    categorical_error: float
    regression_rmse: float
    categorical_count: int
    regression_count: int


def parse_columns(text: str | None) -> list[int]:
    if text is None or text.strip() == "":
        return []
    return sorted({int(part.strip()) for part in text.split(",") if part.strip()})


def gen_nan(x: np.ndarray, drop_fraction: float, seed: int = 42) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return masked copy, original copy, and boolean mask of newly inserted NaNs."""
    if not 0 <= drop_fraction <= 1:
        raise ValueError("drop_fraction must be between 0 and 1.")
    x_original = np.asarray(x, dtype=float).copy()
    x_masked = x_original.copy()
    nan_mask = np.zeros_like(x_masked, dtype=bool)
    if drop_fraction <= 0:
        return x_masked, x_original, nan_mask

    valid_positions = np.argwhere(~np.isnan(x_masked))
    if len(valid_positions) == 0:
        raise ValueError("Cannot add a mask: the input contains no observed values.")

    rng = np.random.default_rng(seed)
    n_new_missing = int(len(valid_positions) * drop_fraction)
    if n_new_missing == 0:
        n_new_missing = 1
    n_new_missing = min(n_new_missing, len(valid_positions))
    chosen = rng.choice(len(valid_positions), size=n_new_missing, replace=False)
    rows = valid_positions[chosen, 0]
    cols = valid_positions[chosen, 1]
    nan_mask[rows, cols] = True
    x_masked[nan_mask] = np.nan
    return x_masked, x_original, nan_mask


def categories_from_columns(x: np.ndarray, categorical_cols: Iterable[int]) -> dict[int, np.ndarray]:
    categories: dict[int, np.ndarray] = {}
    for col in categorical_cols:
        if col < 0 or col >= x.shape[1]:
            raise ValueError(f"Categorical column index out of range: {col}")
        values = x[:, col]
        values = values[~np.isnan(values)]
        if values.size == 0:
            raise ValueError(f"Categorical column {col} has no observed values.")
        categories[col] = np.unique(values)
    return categories


def nearest_category_projection(x_pred: np.ndarray, categories: dict[int, np.ndarray]) -> np.ndarray:
    """Project predicted categorical columns to the nearest known category value."""
    projected = np.asarray(x_pred, dtype=float).copy()
    for col, values in categories.items():
        distances = np.abs(projected[:, col][:, np.newaxis] - values[np.newaxis, :])
        nearest = np.argmin(distances, axis=1)
        projected[:, col] = values[nearest]
    return projected


def mask_prediction_eval(
    x_pred: np.ndarray,
    x_true: np.ndarray,
    mask: np.ndarray,
    categories: dict[int, np.ndarray],
) -> MviMetrics:
    """Compute categorical error rate and continuous RMSE on masked positions only."""
    x_pred = np.asarray(x_pred, dtype=float)
    x_true = np.asarray(x_true, dtype=float)
    mask = np.asarray(mask, dtype=bool)
    if x_pred.shape != x_true.shape or x_true.shape != mask.shape:
        raise ValueError("x_pred, x_true, and mask must have the same shape.")

    projected = nearest_category_projection(x_pred, categories)
    categorical_errors: list[np.ndarray] = []
    regression_residuals: list[np.ndarray] = []

    for col in range(x_true.shape[1]):
        col_mask = mask[:, col]
        if not np.any(col_mask):
            continue
        if col in categories:
            categorical_errors.append(projected[:, col][col_mask] != x_true[:, col][col_mask])
        else:
            regression_residuals.append(projected[:, col][col_mask] - x_true[:, col][col_mask])

    if categorical_errors:
        cat_values = np.concatenate(categorical_errors)
        cat_error = float(np.mean(cat_values))
        cat_count = int(cat_values.size)
    else:
        cat_error = float("nan")
        cat_count = 0

    if regression_residuals:
        reg_values = np.concatenate(regression_residuals)
        reg_rmse = float(np.sqrt(np.mean(reg_values ** 2)))
        reg_count = int(reg_values.size)
    else:
        reg_rmse = float("nan")
        reg_count = 0

    return MviMetrics(cat_error, reg_rmse, cat_count, reg_count)


def simple_column_fill_prediction(x_masked: np.ndarray, categories: dict[int, np.ndarray]) -> np.ndarray:
    """Create a deterministic non-model reconstruction baseline for the demo."""
    pred = np.asarray(x_masked, dtype=float).copy()
    for col in range(pred.shape[1]):
        missing = np.isnan(pred[:, col])
        if not np.any(missing):
            continue
        observed = pred[:, col][~missing]
        if observed.size == 0:
            fill_value = 0.0
        elif col in categories:
            values, counts = np.unique(observed, return_counts=True)
            fill_value = values[np.argmax(counts)]
        else:
            fill_value = float(np.mean(observed))
        pred[missing, col] = fill_value
    return pred


def build_demo_matrix(rows: int, seed: int) -> np.ndarray:
    if rows < 4:
        raise ValueError("Demo requires at least 4 rows.")
    rng = np.random.default_rng(seed)
    categorical = (np.arange(rows) % 3).astype(float)
    trend = np.linspace(0.0, 1.0, rows)
    signal = 0.25 * categorical + trend + rng.normal(0.0, 0.03, size=rows)
    return np.column_stack([categorical, trend, signal]).astype(float)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate and score a tiny deterministic MVI NaN mask fixture.")
    parser.add_argument("--rows", type=int, default=9, help="Rows in the default demo matrix.")
    parser.add_argument("--drop-fraction", type=float, default=0.35, help="Fraction of observed cells to mask with NaN.")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed.")
    parser.add_argument("--categorical-cols", default="0", help="Comma-separated categorical column indices for scoring.")
    parser.add_argument("--print-arrays", action="store_true", help="Print original, masked, mask, and baseline prediction arrays.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    x = build_demo_matrix(args.rows, args.seed)
    categorical_cols = parse_columns(args.categorical_cols)
    x_masked, x_original, nan_mask = gen_nan(x, args.drop_fraction, seed=args.seed)
    categories = categories_from_columns(x_original, categorical_cols)
    pred = simple_column_fill_prediction(x_masked, categories)
    metrics = mask_prediction_eval(pred, x_original, nan_mask, categories)

    print(f"masked_cells={int(nan_mask.sum())}")
    print(f"categorical_cols={categorical_cols}")
    print(f"categorical_error={metrics.categorical_error} over {metrics.categorical_count} masked categorical cells")
    print(f"regression_rmse={metrics.regression_rmse} over {metrics.regression_count} masked continuous cells")

    if args.print_arrays:
        np.set_printoptions(precision=4, suppress=True)
        print("original:\n", x_original)
        print("masked:\n", x_masked)
        print("mask:\n", nan_mask.astype(int))
        print("baseline_prediction:\n", pred)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
