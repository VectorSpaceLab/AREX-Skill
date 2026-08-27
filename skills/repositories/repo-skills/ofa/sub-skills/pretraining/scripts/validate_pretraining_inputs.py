#!/usr/bin/env python3
"""Validate OFA multimodal pretraining input layout.

This helper checks the four TSV families used by the pretraining workflow and
verifies that the negative-sample directory contains the expected files.
It is intentionally lightweight and safe: it only inspects file layout, row
widths, selected columns, and a small amount of payload structure.

Example:
  python validate_pretraining_inputs.py --vision-language-tsv vision_language_examples.tsv \
    --text-tsv text_examples.tsv --image-tsv image_examples.tsv \
    --detection-tsv detection_examples.tsv --negative-sample-dir negative_sample/
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from io import BytesIO
from pathlib import Path
from typing import Iterable, Optional, Sequence

from PIL import Image


def parse_cols(text: Optional[str]) -> list[int]:
    if not text:
        return []
    return [int(item) for item in text.split(",") if item.strip()]


def _ensure_tsv(
    path: Path,
    expected_columns: int,
    selected_cols: Sequence[int],
    image_col: Optional[int] = None,
    int_seq_col: Optional[int] = None,
    max_rows: Optional[int] = None,
) -> int:
    row_count = 0
    with path.open("r", encoding="utf-8") as handle:
        for row_num, raw_line in enumerate(handle, start=1):
            line = raw_line.rstrip("\n")
            if not line:
                raise ValueError(f"{path}: row {row_num} is blank")
            cols = line.split("\t")
            if len(cols) != expected_columns:
                raise ValueError(f"{path}: row {row_num} expected {expected_columns} columns, found {len(cols)}")
            for col in selected_cols:
                if col >= len(cols):
                    raise ValueError(f"{path}: row {row_num} selected col {col} out of range")
            if image_col is not None:
                try:
                    raw = base64.urlsafe_b64decode(cols[image_col])
                    Image.open(BytesIO(raw)).verify()
                except Exception as exc:
                    raise ValueError(f"{path}: row {row_num} image col {image_col} is invalid: {exc}") from exc
            if int_seq_col is not None:
                tokens = cols[int_seq_col].split()
                if not tokens:
                    raise ValueError(f"{path}: row {row_num} code column {int_seq_col} is empty")
                try:
                    for token in tokens:
                        int(token)
                except Exception as exc:
                    raise ValueError(f"{path}: row {row_num} code column {int_seq_col} has a non-integer token: {exc}") from exc
            row_count += 1
            if max_rows is not None and row_count >= max_rows:
                break
    if row_count == 0:
        raise ValueError(f"{path}: file is empty")
    return row_count


def _ensure_negative_samples(path: Path) -> None:
    required = ["all_captions.txt", "object.txt", "type2ans.json"]
    for name in required:
        candidate = path / name
        if not candidate.exists():
            raise ValueError(f"missing negative-sample file: {candidate}")
    with (path / "type2ans.json").open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or "other" not in data:
        raise ValueError("type2ans.json must contain a mapping with an 'other' key")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vision-language-tsv", type=Path, default=None)
    parser.add_argument("--text-tsv", type=Path, default=None)
    parser.add_argument("--image-tsv", type=Path, default=None)
    parser.add_argument("--detection-tsv", type=Path, default=None)
    parser.add_argument("--negative-sample-dir", type=Path, default=None)
    parser.add_argument("--vision-language-selected-cols", default="0,1,2,3,4,5,6,7")
    parser.add_argument("--text-selected-cols", default="0,1")
    parser.add_argument("--image-selected-cols", default="0,1,2")
    parser.add_argument("--detection-selected-cols", default="0,1,2")
    parser.add_argument("--max-rows", type=int, default=None)
    args = parser.parse_args()

    try:
        if args.vision_language_tsv is not None:
            count = _ensure_tsv(
                args.vision_language_tsv,
                expected_columns=8,
                selected_cols=parse_cols(args.vision_language_selected_cols),
                image_col=1,
                max_rows=args.max_rows,
            )
            print(f"vision-language TSV ok: {count} rows")
        if args.text_tsv is not None:
            count = _ensure_tsv(
                args.text_tsv,
                expected_columns=2,
                selected_cols=parse_cols(args.text_selected_cols),
                max_rows=args.max_rows,
            )
            print(f"text TSV ok: {count} rows")
        if args.image_tsv is not None:
            count = _ensure_tsv(
                args.image_tsv,
                expected_columns=3,
                selected_cols=parse_cols(args.image_selected_cols),
                image_col=1,
                int_seq_col=2,
                max_rows=args.max_rows,
            )
            print(f"image TSV ok: {count} rows")
        if args.detection_tsv is not None:
            count = _ensure_tsv(
                args.detection_tsv,
                expected_columns=3,
                selected_cols=parse_cols(args.detection_selected_cols),
                image_col=1,
                max_rows=args.max_rows,
            )
            print(f"detection TSV ok: {count} rows")
        if args.negative_sample_dir is not None:
            _ensure_negative_samples(args.negative_sample_dir)
            print(f"negative-sample dir ok: {args.negative_sample_dir}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
