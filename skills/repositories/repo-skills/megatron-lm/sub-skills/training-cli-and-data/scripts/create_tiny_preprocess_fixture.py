#!/usr/bin/env python3
"""Create a tiny JSONL fixture and print a Megatron preprocessing command."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description="Create a tiny JSONL file for Megatron preprocessing smoke tests.")
    p.add_argument("--directory", default="tiny_megatron_data", help="Directory to create.")
    p.add_argument("--name", default="tiny", help="Fixture basename.")
    p.add_argument("--vocab-size", type=int, default=128)
    args = p.parse_args()

    directory = Path(args.directory)
    directory.mkdir(parents=True, exist_ok=True)
    jsonl = directory / f"{args.name}.jsonl"
    # NullTokenizer tokenizes by splitting on spaces and converting each item to
    # an integer token id. Use numeric strings so the smoke does not require any
    # external tokenizer files or downloads.
    rows = [
        {"text": "1 2 3 4 5"},
        {"text": "6 7 8 9 10"},
    ]
    with jsonl.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    out_prefix = directory / f"{args.name}_out"
    print(f"Wrote {jsonl}")
    print("Run from a Megatron-LM checkout or environment that provides the preprocessing tool:")
    print(
        "python tools/preprocess_data.py "
        f"--input {jsonl} --output-prefix {out_prefix} "
        "--tokenizer-type NullTokenizer "
        f"--vocab-size {args.vocab_size} --workers 1 --append-eod --json-keys text"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
