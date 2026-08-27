#!/usr/bin/env python3
"""Validate the PAWS-X TSV layout and cache directory."""

from __future__ import annotations

import argparse
from pathlib import Path

import transformers


LANGS = ["en", "zh", "de", "es"]
SPLITS = ["train", "dev", "test"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Check the PAWS-X data layout")
    parser.add_argument("root", type=Path, help="path to the pawsx dataset root")
    parser.add_argument(
        "--cache-model",
        default="bert-base-multilingual-cased",
        help="model name used when naming cached_feature files",
    )
    parser.add_argument("--max-length", type=int, default=128, help="max sequence length used for cache naming")
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"missing dataset root: {root}")

    if not hasattr(transformers, 'AdamW'):
        raise SystemExit('transformers.AdamW is unavailable; use a compatible 4.x release')
    if not hasattr(transformers, 'DataProcessor'):
        raise SystemExit('transformers.DataProcessor is unavailable; use a compatible 4.x release')
    print(f"transformers version: {transformers.__version__}")

    missing = []
    for lang in LANGS:
        for split in SPLITS:
            tsv = root / f"{split}-{lang}.tsv"
            if not tsv.is_file():
                missing.append(tsv.name)
                continue
            line_count = sum(1 for _ in tsv.open("r", encoding="utf-8"))
            print(f"{tsv.name}: {line_count} lines")
            if line_count == 0:
                missing.append(tsv.name)

    if missing:
        raise SystemExit(f"missing or empty TSV files: {', '.join(missing)}")

    cache_hint = root / f"cached_feature_train_en_{args.cache_model}_{args.max_length}"
    print(f"cache hint: {cache_hint.name}")
    print("paws-x data layout: ok")


if __name__ == "__main__":
    main()
