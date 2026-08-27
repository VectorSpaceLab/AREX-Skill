#!/usr/bin/env python3
"""Smoke-test CrossEncoder pair scoring and reranking.

This helper is adapted from the sentence-transformers CrossEncoder usage and
reranking examples into a self-contained CLI. It performs no model loading for
`--help`; a model is loaded only when `--model` is supplied.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Score query-document pairs and rerank documents with sentence-transformers CrossEncoder.",
    )
    parser.add_argument(
        "--model",
        help="CrossEncoder model id or local model directory. Required to run inference.",
    )
    parser.add_argument(
        "--query",
        default="How many people live in Berlin?",
        help="Query text to pair with every document.",
    )
    parser.add_argument(
        "--documents",
        nargs="+",
        default=[
            "Berlin had 3,520,031 registered inhabitants in 2019.",
            "Berlin is well known for its museums.",
            "The urban area of Berlin comprised about 4.1 million people in 2014.",
        ],
        help="Candidate documents to rerank. Pass one or more strings.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of ranked documents to print. Use 0 to return all candidates.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="CrossEncoder inference batch size.",
    )
    parser.add_argument(
        "--device",
        help="Optional device string such as cpu, cuda, cuda:0, mps, or npu.",
    )
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="Only load models from the local Hugging Face/cache files; do not download.",
    )
    parser.add_argument(
        "--return-documents",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include document text in rank output.",
    )
    parser.add_argument(
        "--predict-pairs",
        action="store_true",
        help="Also call predict on explicit (query, document) pairs before rank.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a human-readable table.",
    )
    return parser


def normalize_score(score: Any) -> Any:
    if hasattr(score, "item"):
        return score.item()
    if hasattr(score, "tolist"):
        return score.tolist()
    return score


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.top_k < 0:
        parser.error("--top-k must be non-negative")
    if args.batch_size <= 0:
        parser.error("--batch-size must be positive")
    if not args.documents:
        parser.error("--documents must contain at least one document")
    if not args.model:
        parser.error("--model is required to run inference; use --help for usage without loading a model")

    try:
        from sentence_transformers import CrossEncoder
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"Failed to import sentence_transformers.CrossEncoder: {exc}", file=sys.stderr)
        return 2

    try:
        model_kwargs: dict[str, Any] = {"local_files_only": args.local_files_only}
        if args.device:
            model_kwargs["device"] = args.device
        model = CrossEncoder(args.model, **model_kwargs)

        top_k = None if args.top_k == 0 else args.top_k
        ranked = model.rank(
            args.query,
            args.documents,
            top_k=top_k,
            return_documents=args.return_documents,
            batch_size=args.batch_size,
            show_progress_bar=False,
        )
    except Exception as exc:  # pragma: no cover - model/backend dependent
        print(f"CrossEncoder rerank failed: {exc}", file=sys.stderr)
        return 1

    output: dict[str, Any] = {
        "model": args.model,
        "query": args.query,
        "ranked": [
            {key: normalize_score(value) for key, value in row.items()}
            for row in ranked
        ],
    }

    if args.predict_pairs:
        try:
            pair_scores = model.predict(
                [(args.query, document) for document in args.documents],
                batch_size=args.batch_size,
                show_progress_bar=False,
            )
            output["pair_scores"] = [normalize_score(score) for score in pair_scores]
        except Exception as exc:  # pragma: no cover - model/backend dependent
            print(f"CrossEncoder predict failed: {exc}", file=sys.stderr)
            return 1

    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"Query: {args.query}")
        for index, row in enumerate(output["ranked"], start=1):
            corpus_id = row["corpus_id"]
            score = row["score"]
            text = row.get("text", args.documents[corpus_id])
            print(f"{index}. corpus_id={corpus_id}\tscore={score}\t{text}")
        if "pair_scores" in output:
            print("\nPair scores:")
            for index, score in enumerate(output["pair_scores"]):
                print(f"{index}. score={score}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
