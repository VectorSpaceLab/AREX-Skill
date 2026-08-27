#!/usr/bin/env python3
"""Create a tiny FlagEmbedding custom retrieval dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


CORPUS = [
    {
        "id": "doc-eval",
        "title": "Evaluation data",
        "text": "FlagEmbedding custom evaluation reads a corpus, queries, and qrels from JSONL files.",
    },
    {
        "id": "doc-rerank",
        "title": "Reranking",
        "text": "A reranker scores the top retrieved query and document pairs after dense retrieval.",
    },
    {
        "id": "doc-cache",
        "title": "Corpus cache",
        "text": "Saved corpus embeddings can be reused when the model and corpus have not changed.",
    },
    {
        "id": "doc-negative",
        "title": "Cooking note",
        "text": "This unrelated document is included to make the retrieval fixture nontrivial.",
    },
]

QUERIES = [
    {
        "id": "q-eval",
        "text": "What files are needed for custom retrieval evaluation?",
    },
    {
        "id": "q-rerank",
        "text": "What component scores top retrieved document pairs?",
    },
]

QRELS = [
    {"qid": "q-eval", "docid": "doc-eval", "relevance": 1},
    {"qid": "q-eval", "docid": "doc-cache", "relevance": 1},
    {"qid": "q-eval", "docid": "doc-negative", "relevance": 0},
    {"qid": "q-rerank", "docid": "doc-rerank", "relevance": 1},
    {"qid": "q-rerank", "docid": "doc-negative", "relevance": 0},
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create corpus.jsonl, <split>_queries.jsonl, and "
            "<split>_qrels.jsonl for a tiny custom retrieval dataset."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("tiny_retrieval_dataset"),
        help="Directory where the JSONL files will be written.",
    )
    parser.add_argument(
        "--split",
        default="test",
        help="Split name used in <split>_queries.jsonl and <split>_qrels.jsonl.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing fixture files in the output directory.",
    )
    return parser.parse_args()


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]], overwrite: bool) -> int:
    if path.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")

    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")
            count += 1
    return count


def main() -> None:
    args = parse_args()
    if not args.split or any(sep in args.split for sep in ("/", "\\")):
        raise ValueError("--split must be a non-empty file-name component")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = [
        (args.output_dir / "corpus.jsonl", CORPUS),
        (args.output_dir / f"{args.split}_queries.jsonl", QUERIES),
        (args.output_dir / f"{args.split}_qrels.jsonl", QRELS),
    ]

    for path, rows in outputs:
        count = write_jsonl(path, rows, overwrite=args.overwrite)
        print(f"wrote {count} rows to {path}")


if __name__ == "__main__":
    main()
