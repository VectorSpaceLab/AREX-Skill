#!/usr/bin/env python3
"""Run a bounded bm25s.high_level file-search example.

With no --input, the script creates a temporary TXT fixture. An explicit
--input is read in place and is never modified.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Sequence

import bm25s.high_level as bm25


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Load a local TXT/CSV/JSON/JSONL file and run one high-level search."
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Existing local input file; omit to use a temporary TXT fixture.",
    )
    parser.add_argument(
        "--document-column",
        help="CSV column or JSON/JSONL key containing document text.",
    )
    parser.add_argument("--query", default="fast", help="Query text (default: fast).")
    parser.add_argument(
        "-k",
        "--top-k",
        type=int,
        default=3,
        help="Nonnegative result count (default: 3).",
    )
    return parser


def run(input_path: Path, query: str, top_k: int, document_column: str | None) -> dict:
    if not input_path.exists():
        raise FileNotFoundError(f"input file not found: {input_path}")
    if top_k < 0:
        raise ValueError("top-k must be nonnegative")

    documents = bm25.load(input_path, document_column=document_column)
    if not isinstance(documents, list):
        raise TypeError("the loader did not return a document list")
    searcher = bm25.index(documents)
    hits = searcher.search([query], k=top_k)
    return {
        "input": str(input_path),
        "documents": len(documents),
        "query": query,
        "results": hits[0],
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.input is not None:
        report = run(args.input, args.query, args.top_k, args.document_column)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    with tempfile.TemporaryDirectory(prefix="bm25s-high-level-") as temp_dir:
        fixture = Path(temp_dir) / "documents.txt"
        fixture.write_text(
            "Machine learning searches text.\n"
            "Deep learning uses neural networks.\n"
            "A small lexical search fixture is fast.\n",
            encoding="utf-8",
        )
        report = run(fixture, args.query, args.top_k, args.document_column)
        report["input"] = "<temporary fixture>"
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
