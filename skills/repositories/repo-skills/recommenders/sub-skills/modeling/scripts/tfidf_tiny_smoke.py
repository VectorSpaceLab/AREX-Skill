#!/usr/bin/env python3
"""Deterministic tiny TF-IDF recommender smoke check.

The default tokenization method is "none" to avoid network/cache assumptions.
The script uses an in-memory item-text fixture, writes no files, and performs no
long training.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Iterable

import pandas as pd

TOKENIZATION_METHODS = ["none", "nltk", "bert", "scibert"]
ID_COL = "item_id"
TEXT_COLS = ["title", "abstract"]
CLEAN_COL = "cleaned_text"


def build_items() -> pd.DataFrame:
    return pd.DataFrame(
        {
            ID_COL: ["paper-a", "paper-b", "paper-c", "paper-d"],
            "title": [
                "graph neural recommenders",
                "graph embeddings for ranking",
                "kitchen recipe retrieval",
                "neural collaborative filtering",
            ],
            "abstract": [
                "collaborative filtering on user item graphs",
                "ranking items with graph representation learning",
                "ingredients and cooking instructions for recipes",
                "matrix factorization with neural networks for user item scores",
            ],
        }
    )


def validate_recommendations(recs: pd.DataFrame, requested_k: int) -> dict:
    expected_cols = [ID_COL, "rec_rank", "rec_score", f"rec_{ID_COL}"]
    missing = [col for col in expected_cols if col not in recs.columns]
    if missing:
        raise AssertionError(f"TF-IDF output is missing columns: {missing}")
    if recs.empty:
        raise AssertionError("TF-IDF recommendation output is empty")
    self_recs = recs[recs[ID_COL] == recs[f"rec_{ID_COL}"]]
    if not self_recs.empty:
        raise AssertionError("TF-IDF output contains self-recommendations")
    max_per_item = int(recs.groupby(ID_COL).size().max())
    if max_per_item > requested_k:
        raise AssertionError(f"item has {max_per_item} recommendations, expected <= {requested_k}")
    if not pd.api.types.is_numeric_dtype(recs["rec_score"]):
        raise AssertionError("rec_score must be numeric")
    return {
        "rows": int(len(recs)),
        "items": int(recs[ID_COL].nunique()),
        "max_rows_per_item": max_per_item,
        "self_recommendations": int(len(self_recs)),
        "columns": expected_cols,
    }


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
        description="Run a tiny no-network TF-IDF item-to-item recommendation smoke check."
    )
    parser.add_argument(
        "--top-k",
        type=positive_int,
        default=1,
        help="Recommendations per item. Must be less than the number of fixture items.",
    )
    parser.add_argument(
        "--tokenization",
        choices=TOKENIZATION_METHODS,
        default="none",
        help="Tokenization method. Default 'none' avoids tokenizer downloads and NLTK resource assumptions.",
    )
    parser.add_argument(
        "--ngram-max",
        type=positive_int,
        default=2,
        help="Upper n-gram size for the TF-IDF vectorizer.",
    )
    args = parser.parse_args(list(argv))
    if args.top_k >= len(build_items()):
        parser.error("--top-k must be less than the number of fixture items")
    if args.ngram_max < 1:
        parser.error("--ngram-max must be >= 1")
    return args


def main(argv: Iterable[str] = sys.argv[1:]) -> int:
    args = parse_args(argv)
    try:
        from recommenders.models.tfidf.tfidf_utils import TfidfRecommender
    except Exception as exc:  # pragma: no cover - depends on user's install
        print(
            "Cannot import recommenders.models.tfidf.tfidf_utils.TfidfRecommender. Install the base recommenders package before running this smoke check.\n"
            f"Original error: {exc}",
            file=sys.stderr,
        )
        return 2

    try:
        items = build_items()
        recommender = TfidfRecommender(id_col=ID_COL, tokenization_method=args.tokenization)
        clean = recommender.clean_dataframe(items.copy(), TEXT_COLS, new_col_name=CLEAN_COL)
        if clean[CLEAN_COL].str.strip().eq("").all():
            raise AssertionError("all cleaned text rows are empty")
        tf, vectors = recommender.tokenize_text(
            clean,
            text_col=CLEAN_COL,
            ngram_range=(1, args.ngram_max),
            min_df=0.0,
        )
        recommender.fit(tf, vectors)
        recs = recommender.recommend_top_k_items(clean, k=args.top_k)
        summary = validate_recommendations(recs, args.top_k)
        tokens = recommender.get_tokens()
        if not isinstance(tokens, dict) or not tokens:
            raise AssertionError("expected a non-empty TF-IDF vocabulary")
        detail = recommender.get_top_k_recommendations(
            clean,
            query_id=items[ID_COL].iloc[0],
            cols_to_keep=["title"],
            verbose=False,
        )
        detail_rows = len(getattr(detail, "data", detail))
        summary.update(
            {
                "status": "ok",
                "model": "TfidfRecommender",
                "tokenization_method": args.tokenization,
                "vocabulary_size": int(len(tokens)),
                "detail_rows_for_first_item": int(detail_rows),
            }
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        hint = ""
        if args.tokenization in {"bert", "scibert"}:
            hint = " Try --tokenization none unless tokenizer assets are already available."
        elif args.tokenization == "nltk":
            hint = " Try --tokenization none if NLTK tokenizer data is unavailable."
        print(f"TF-IDF tiny smoke failed: {exc}.{hint}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
