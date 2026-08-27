#!/usr/bin/env python3
"""Tiny no-network smoke check for Recommenders Python evaluation metrics."""

from __future__ import annotations

import argparse
import json
import math
import sys

import pandas as pd


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run tiny Recommenders metric checks on in-memory dataframes.")
    parser.add_argument("--k", type=positive_int, default=2, help="Top-k value for ranking metrics.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        from recommenders.evaluation.python_evaluation import (
            mae,
            map_at_k,
            ndcg_at_k,
            precision_at_k,
            recall_at_k,
            rmse,
        )
    except Exception as exc:
        print(f"Cannot import Recommenders Python evaluation metrics: {exc}", file=sys.stderr)
        return 2

    rating_true = pd.DataFrame(
        {
            "userID": [1, 1, 2, 2, 3],
            "itemID": [1, 2, 1, 3, 2],
            "rating": [5.0, 4.0, 1.0, 5.0, 4.0],
        }
    )
    rating_pred = pd.DataFrame(
        {
            "userID": [1, 1, 2, 2, 3],
            "itemID": [1, 2, 1, 3, 2],
            "prediction": [4.8, 3.9, 1.2, 4.5, 3.5],
        }
    )
    ranking_pred = pd.DataFrame(
        {
            "userID": [1, 1, 1, 2, 2, 2, 3, 3],
            "itemID": [1, 3, 2, 3, 4, 1, 2, 5],
            "prediction": [0.99, 0.80, 0.20, 0.90, 0.50, 0.10, 0.95, 0.30],
        }
    )

    values = {
        "rmse": float(rmse(rating_true, rating_pred)),
        "mae": float(mae(rating_true, rating_pred)),
        f"precision@{args.k}": float(precision_at_k(rating_true, ranking_pred, k=args.k, threshold=4)),
        f"recall@{args.k}": float(recall_at_k(rating_true, ranking_pred, k=args.k, threshold=4)),
        f"ndcg@{args.k}": float(ndcg_at_k(rating_true, ranking_pred, k=args.k, threshold=4)),
        f"map@{args.k}": float(map_at_k(rating_true, ranking_pred, k=args.k, threshold=4)),
    }
    for name, value in values.items():
        if not math.isfinite(value):
            print(f"metric {name} is not finite: {value}", file=sys.stderr)
            return 1
        if "@" in name and not 0.0 <= value <= 1.0:
            print(f"ranking metric {name} outside [0, 1]: {value}", file=sys.stderr)
            return 1
    print(json.dumps({"status": "ok", "metrics": values}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
