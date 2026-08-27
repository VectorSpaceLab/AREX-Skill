#!/usr/bin/env python3
"""Create a tiny local bm25s index suitable for bounded MCP checks.

This script never contacts Hugging Face, BEIR, or an MCP transport.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def build_fixture(output_dir: Path, overwrite: bool = False) -> dict[str, object]:
    """Save a small corpus-backed index and return its local summary."""
    if output_dir.exists() and any(output_dir.iterdir()):
        if not overwrite:
            raise SystemExit(
                f"Refusing non-empty output directory: {output_dir}. "
                "Choose a fresh directory or pass --overwrite explicitly."
            )
        if not output_dir.is_dir():
            raise SystemExit(f"Refusing to overwrite a non-directory path: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    import bm25s

    corpus = [
        {"id": "d-red", "text": "red fox near the quiet forest"},
        {"id": "d-blue", "text": "blue fish swims in a clear lake"},
        {"id": "d-green", "text": "green bird rests in a forest tree"},
        {"id": "d-yellow", "text": "yellow sun shines over the lake"},
    ]
    texts = [record["text"] for record in corpus]
    retriever = bm25s.BM25()
    retriever.index(bm25s.tokenize(texts), show_progress=False)
    retriever.save(output_dir, corpus=corpus, show_progress=False)

    summary = {
        "index_dir": str(output_dir),
        "documents": len(corpus),
        "corpus_file": str(output_dir / "corpus.jsonl"),
    }
    (output_dir / "fixture-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    summary["files"] = sorted(path.name for path in output_dir.iterdir())
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a four-document local BM25S index for MCP fixture checks."
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Destination for the local index and corpus.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing non-empty destination after explicit confirmation.",
    )
    args = parser.parse_args()
    summary = build_fixture(args.output_dir, overwrite=args.overwrite)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
