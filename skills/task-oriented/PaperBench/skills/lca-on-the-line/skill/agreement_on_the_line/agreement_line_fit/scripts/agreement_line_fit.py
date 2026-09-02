#!/usr/bin/env python3
"""Fit probit-space agreement-on-the-line diagnostics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def fit_line_from_stats(stats: dict, r2_threshold: float = 0.95) -> dict:
    pairs = stats["pairwise_probit"]
    if len(pairs) < 3:
        raise ValueError("at least three pairwise observations are required")
    xs = [entry["id_agreement"] for entry in pairs.values()]
    ys = [entry["ood_agreement"] for entry in pairs.values()]
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    denom = sum((x - x_mean) ** 2 for x in xs)
    if denom <= 1e-12:
        raise ValueError("ID agreement values are constant; line fit is ill-conditioned")
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denom
    intercept = y_mean - slope * x_mean
    predictions = [slope * x + intercept for x in xs]
    residuals = [y - pred for y, pred in zip(ys, predictions)]
    ss_res = sum(r * r for r in residuals)
    ss_tot = sum((y - y_mean) ** 2 for y in ys)
    r2 = 1.0 if ss_tot <= 1e-12 and ss_res <= 1e-12 else 1.0 - ss_res / ss_tot
    return {
        "slope": slope,
        "intercept": intercept,
        "r2": r2,
        "pair_count": len(pairs),
        "on_line": bool(r2 >= r2_threshold),
        "r2_threshold": r2_threshold,
        "residual_max_abs": max(abs(r) for r in residuals),
        "residual_mean_abs": sum(abs(r) for r in residuals) / len(residuals),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stats")
    parser.add_argument("--output", required=True)
    parser.add_argument("--r2-threshold", type=float, default=0.95)
    args = parser.parse_args()
    stats = json.loads(Path(args.stats).read_text())
    result = fit_line_from_stats(stats, args.r2_threshold)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
