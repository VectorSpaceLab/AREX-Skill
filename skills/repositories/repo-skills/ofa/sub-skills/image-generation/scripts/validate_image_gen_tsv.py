#!/usr/bin/env python3
"""Validate OFA text-to-image generation TSV layouts.

The image-generation workflow accepts 2-, 3-, or 4-column rows depending on
whether an image base64 payload and/or image code sequence is present. This
helper checks row width, selected columns, base64 image payloads, and integer
code sequences before any GPU generation or VQGAN conversion.

Example:
  python validate_image_gen_tsv.py --file coco_vqgan_train.tsv --expected-code-length 1024
"""

from __future__ import annotations

import argparse
import base64
import sys
from io import BytesIO
from pathlib import Path
from typing import Optional, Sequence

from PIL import Image


def parse_cols(text: Optional[str]) -> list[int]:
    if not text:
        return []
    return [int(item) for item in text.split(",") if item.strip()]


def _validate_row(
    cols: Sequence[str],
    row_num: int,
    selected_cols: Sequence[int],
    expected_code_length: Optional[int],
) -> None:
    if len(cols) not in {2, 3, 4}:
        raise ValueError(f"row {row_num}: expected 2, 3, or 4 columns, found {len(cols)}")
    for col in selected_cols:
        if col >= len(cols):
            raise ValueError(f"row {row_num}: selected column {col} out of range for row length {len(cols)}")

    if len(cols) == 4:
        try:
            raw = base64.urlsafe_b64decode(cols[1])
            Image.open(BytesIO(raw)).verify()
        except Exception as exc:
            raise ValueError(f"row {row_num}: image column 1 is not a valid base64 image: {exc}") from exc

    code_col = 2 if len(cols) == 3 else 3 if len(cols) == 4 else None
    if code_col is not None:
        tokens = [token for token in cols[code_col].split() if token]
        if not tokens:
            raise ValueError(f"row {row_num}: image code column {code_col} is empty")
        try:
            for token in tokens:
                int(token)
        except Exception as exc:
            raise ValueError(f"row {row_num}: image code column {code_col} contains a non-integer token: {exc}") from exc
        if expected_code_length is not None and len(tokens) != expected_code_length:
            raise ValueError(
                f"row {row_num}: expected image code length {expected_code_length}, found {len(tokens)}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True, type=Path, help="Image-generation TSV file to validate.")
    parser.add_argument("--selected-cols", default=None, help="Comma-separated selected column indices.")
    parser.add_argument("--expected-code-length", type=int, default=None, help="Expected number of integer code tokens.")
    parser.add_argument("--max-rows", type=int, default=None, help="Stop after this many rows.")
    args = parser.parse_args()

    try:
        row_count = 0
        with args.file.open("r", encoding="utf-8") as handle:
            for row_num, raw_line in enumerate(handle, start=1):
                line = raw_line.rstrip("\n")
                if not line:
                    raise ValueError(f"row {row_num}: blank line encountered")
                cols = line.split("\t")
                _validate_row(cols, row_num, parse_cols(args.selected_cols), args.expected_code_length)
                row_count += 1
                if args.max_rows is not None and row_count >= args.max_rows:
                    break
        if row_count == 0:
            raise ValueError(f"{args.file}: file is empty")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"validated {row_count} rows in {args.file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
