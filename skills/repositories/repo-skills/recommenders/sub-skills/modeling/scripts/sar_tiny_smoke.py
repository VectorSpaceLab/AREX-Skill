#!/usr/bin/env python3
"""Deterministic tiny SAR smoke check for the Recommenders modeling skill.

The script uses an in-memory implicit-feedback fixture. It performs no network
access, writes no files, and trains only a tiny CPU SAR model.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Iterable

import pandas as pd

SIMILARITIES = [
    "cooccurrence",
    "cosine",
    "inclusion index",
    "jaccard",
    "lexicographers mutual information",
    "lift",
    "mutual information",
]


def build_train() -> pd.DataFrame:
    """Return a small interaction fixture with two unseen candidates per user."""
    return pd.DataFrame(
        {
            "userID": ["u1", "u1", "u2", "u2", "u3", "u3", "u4", "u4"],
            "itemID": ["i1", "i2", "i1", "i3", "i2", "i4", "i3", "i4"],
            "rating": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            "timestamp": [1, 2, 1, 3, 2, 4, 3, 4],
        }
    )


def seen_pairs(df: pd.DataFrame) -> set[tuple[str, str]]:
    return set(zip(df["userID"].astype(str), df["itemID"].astype(str)))


def validate_top_k(top_k: pd.DataFrame, train: pd.DataFrame, requested_k: int) -> dict:
    expected_cols = ["userID", "itemID", "prediction"]
    missing = [col for col in expected_cols if col not in top_k.columns]
    if missing:
        raise AssertionError(f"top-k output is missing columns: {missing}")
    if top_k.empty:
        raise AssertionError("top-k output is empty; fixture should produce novel recommendations")
    overlap = seen_pairs(top_k) & seen_pairs(train)
    if overlap:
        raise AssertionError(f"remove_seen=True leaked seen interactions: {sorted(overlap)}")
    max_per_user = int(top_k.groupby("userID").size().max())
    if max_per_user > requested_k:
        raise AssertionError(f"top-k output has {max_per_user} rows for a user, expected <= {requested_k}")
    return {
        "rows": int(len(top_k)),
        "users": int(top_k["userID"].nunique()),
        "max_rows_per_user": max_per_user,
        "remove_seen_ok": True,
        "columns": expected_cols,
    }


def run_duplicate_check(similarity: str) -> dict:
    from recommenders.models.sar import SAR

    train = build_train()
    duplicated = pd.concat([train, train.iloc[[0]]], ignore_index=True)
    model = SAR(similarity_type=similarity)
    try:
        model.fit(duplicated)
    except ValueError as exc:
        if "duplicates" not in str(exc).lower():
            raise AssertionError(f"duplicate check raised unexpected ValueError: {exc}") from exc
        return {"status": "ok", "expected_duplicate_error": True, "message": str(exc)}
    raise AssertionError("SAR accepted a duplicated training dataframe; expected ValueError")


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return parsed


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny no-network SAR fit/predict/recommend smoke check."
    )
    parser.add_argument(
        "--top-k",
        type=positive_int,
        default=2,
        help="Recommendations per user for the fixture. The bundled fixture supports at most 2 novel items per user.",
    )
    parser.add_argument(
        "--similarity",
        choices=SIMILARITIES,
        default="jaccard",
        help="SAR item-item similarity type to use.",
    )
    parser.add_argument(
        "--time-decay",
        action="store_true",
        help="Enable SAR time decay using the fixture timestamp column.",
    )
    parser.add_argument(
        "--expect-duplicate-error",
        action="store_true",
        help="Instead of the normal smoke, verify that SAR rejects duplicated training rows.",
    )
    args = parser.parse_args(list(argv))
    if args.top_k > 2:
        parser.error("the bundled fixture has only 2 novel candidate items per user; use --top-k 1 or 2")
    return args


def main(argv: Iterable[str] = sys.argv[1:]) -> int:
    args = parse_args(argv)
    try:
        from recommenders.models.sar import SAR
    except Exception as exc:  # pragma: no cover - depends on user's install
        print(
            "Cannot import recommenders.models.sar.SAR. Install the base recommenders package before running this smoke check.\n"
            f"Original error: {exc}",
            file=sys.stderr,
        )
        return 2

    try:
        if args.expect_duplicate_error:
            print(json.dumps(run_duplicate_check(args.similarity), indent=2, sort_keys=True))
            return 0

        train = build_train()
        model = SAR(
            col_user="userID",
            col_item="itemID",
            col_rating="rating",
            col_timestamp="timestamp",
            similarity_type=args.similarity,
            timedecay_formula=args.time_decay,
            threshold=1,
        )
        model.fit(train)

        test_users = train[["userID"]].drop_duplicates().reset_index(drop=True)
        top_k = model.recommend_k_items(test_users, top_k=args.top_k, remove_seen=True)
        pair_scores = model.predict(
            pd.DataFrame({"userID": ["u1", "u2"], "itemID": ["i3", "i4"]})
        )
        summary = validate_top_k(top_k, train, args.top_k)
        summary.update(
            {
                "status": "ok",
                "model": "SAR",
                "similarity": args.similarity,
                "time_decay": bool(args.time_decay),
                "pair_prediction_rows": int(len(pair_scores)),
                "pair_prediction_columns": list(pair_scores.columns),
            }
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"SAR tiny smoke failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
