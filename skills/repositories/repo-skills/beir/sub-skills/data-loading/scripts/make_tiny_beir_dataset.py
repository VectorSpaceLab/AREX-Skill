#!/usr/bin/env python3
"""Create a tiny offline BEIR-format dataset fixture.

Examples:
    python make_tiny_beir_dataset.py ./tiny-beir
    python make_tiny_beir_dataset.py ./tiny-beir --force

The generated fixture contains corpus.jsonl, queries.jsonl, and qrels/test.tsv.
It performs no network access and imports no BEIR package modules.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


CORPUS_ROWS = [
    {
        "_id": "doc1",
        "title": "Albert Einstein",
        "text": "Albert Einstein developed the theory of relativity and studied the photoelectric effect.",
    },
    {
        "_id": "doc2",
        "title": "Wheat beer",
        "text": "Wheat beer is brewed with a large proportion of wheat relative to malted barley.",
    },
]

QUERY_ROWS = [
    {"_id": "q1", "text": "Who developed the theory of relativity?"},
    {"_id": "q2", "text": "Which beer uses a large proportion of wheat?"},
]

QRELS_ROWS = [
    ("q1", "doc1", 1),
    ("q2", "doc2", 1),
]


def write_jsonl(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            json.dump(row, handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a tiny local BEIR-format dataset fixture.")
    parser.add_argument("output_dir", type=Path, help="Directory where the fixture should be created.")
    parser.add_argument("--split", default="test", help="Qrels split filename to create, without .tsv. Default: test.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite corpus/query/qrels files if they already exist.",
    )
    return parser.parse_args()


def fail(message: str) -> None:
    raise SystemExit(f"error: {message}")


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    qrels_dir = output_dir / "qrels"
    qrels_file = qrels_dir / f"{args.split}.tsv"
    files = [output_dir / "corpus.jsonl", output_dir / "queries.jsonl", qrels_file]

    if args.split == "" or "/" in args.split or "\\" in args.split:
        fail("--split must be a non-empty filename stem such as 'test' or 'dev'")

    existing = [path for path in files if path.exists()]
    if existing and not args.force:
        joined = ", ".join(str(path) for path in existing)
        fail(f"refusing to overwrite existing file(s): {joined}; pass --force to replace them")

    qrels_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / "corpus.jsonl", CORPUS_ROWS)
    write_jsonl(output_dir / "queries.jsonl", QUERY_ROWS)

    with qrels_file.open("w", encoding="utf-8", newline="") as handle:
        handle.write("query-id\tcorpus-id\tscore\n")
        for query_id, corpus_id, score in QRELS_ROWS:
            handle.write(f"{query_id}\t{corpus_id}\t{score}\n")

    print(f"Created tiny BEIR dataset at {output_dir}")
    print(f"Validate with: python validate_beir_dataset.py {output_dir} --split {args.split}")


if __name__ == "__main__":
    main()
