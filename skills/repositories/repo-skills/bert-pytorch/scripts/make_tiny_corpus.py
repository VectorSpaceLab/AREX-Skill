#!/usr/bin/env python3
"""Create a deterministic two-line tab-separated corpus fixture."""

from __future__ import annotations

import argparse
from pathlib import Path

TINY_CORPUS_LINES = [
    "Welcome to the\tthe jungle",
    "I can stay\there all night",
]


def write_tiny_corpus(path: Path, overwrite: bool = False) -> Path:
    path = path.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} already exists; pass --overwrite to replace it")
    path.write_text("\n".join(TINY_CORPUS_LINES) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a known-good BERT-pytorch corpus fixture.")
    parser.add_argument("--output", required=True, help="Target corpus path.")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing output file.")
    args = parser.parse_args()

    output = write_tiny_corpus(Path(args.output), overwrite=args.overwrite)
    print(output)
    print(f"{len(TINY_CORPUS_LINES)} lines written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
