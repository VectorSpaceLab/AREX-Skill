#!/usr/bin/env python3
"""Run a deterministic, no-network smoke test for rank_bm25.

The helper uses a tiny in-memory corpus and the installed public package. It
writes no files and is safe to run from any current working directory.
Example: python scripts/smoke_rank_bm25.py --variant bm25plus --top-n 2
"""

from __future__ import annotations

import argparse
from typing import Type

import numpy as np
from rank_bm25 import BM25L, BM25Okapi, BM25Plus


VARIANTS: dict[str, Type[object]] = {
    "okapi": BM25Okapi,
    "bm25l": BM25L,
    "bm25plus": BM25Plus,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke-test rank_bm25 with a tiny in-memory corpus."
    )
    parser.add_argument(
        "--variant",
        choices=["all", *VARIANTS],
        default="all",
        help="Concrete BM25 variant to check (default: all).",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=1,
        help="Number of documents to retrieve (default: 1).",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.top_n < 1:
        raise SystemExit("--top-n must be at least 1")

    documents = [
        "Hello there good man!",
        "It is quite windy in London",
        "How is the weather today?",
    ]
    tokenized_documents = [document.split() for document in documents]
    tokenized_query = "windy London".split()
    names = VARIANTS if args.variant == "all" else {args.variant: VARIANTS[args.variant]}

    for name, cls in names.items():
        index = cls(tokenized_documents)
        scores = index.get_scores(tokenized_query)
        assert isinstance(scores, np.ndarray), type(scores)
        assert scores.shape == (len(documents),), scores.shape

        top_documents = index.get_top_n(tokenized_query, documents, n=args.top_n)
        assert top_documents[0] == documents[1], top_documents

        candidate_ids = [1, 2]
        batch_scores = index.get_batch_scores(tokenized_query, candidate_ids)
        assert isinstance(batch_scores, list), type(batch_scores)
        assert len(batch_scores) == len(candidate_ids), batch_scores
        assert batch_scores[0] > batch_scores[1], batch_scores
        print(f"{name}: ok; top={top_documents[0]!r}; scores={scores.tolist()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
