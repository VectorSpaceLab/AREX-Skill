#!/usr/bin/env python3
"""Validate OFA-style TSV rows and common column encodings.

The helper is intentionally generic so that caption, VQA, RefCOCO, OCR,
ImageNet, Gigaword, GLUE, pretraining, and MMSpeech layouts can share one
small validator. It checks row width, selected column indices, optional base64
payloads, optional image decoding, integer-token sequences, JSON cells, and
filesystem path cells.

Example:
  python validate_ofa_tsv.py --file caption.tsv --expect-columns 5 \
    --selected-cols 1,4,2 --base64-cols 4 --image-cols 4
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from io import BytesIO
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from PIL import Image


def parse_col_list(value: Optional[str]) -> List[int]:
    if not value:
        return []
    return [int(item) for item in value.split(",") if item.strip()]


def parse_int_set(value: Optional[str]) -> Optional[set[int]]:
    if not value:
        return None
    return {int(item) for item in value.split(",") if item.strip()}


def _fail(message: str) -> None:
    raise ValueError(message)


def _check_base64(cell: str, row_num: int, col: int) -> None:
    try:
        base64.urlsafe_b64decode(cell)
    except Exception as exc:
        _fail(f"row {row_num}: column {col} is not valid URL-safe base64: {exc}")


def _check_image(cell: str, row_num: int, col: int) -> None:
    try:
        raw = base64.urlsafe_b64decode(cell)
        Image.open(BytesIO(raw)).verify()
    except Exception as exc:
        _fail(f"row {row_num}: column {col} is not a decodable image: {exc}")


def _check_int_sequence(cell: str, row_num: int, col: int) -> None:
    tokens = [token for token in cell.split() if token]
    if not tokens:
        _fail(f"row {row_num}: column {col} is an empty integer sequence")
    try:
        for token in tokens:
            int(token)
    except Exception as exc:
        _fail(f"row {row_num}: column {col} contains a non-integer token: {exc}")


def _check_json(cell: str, row_num: int, col: int) -> None:
    try:
        json.loads(cell)
    except Exception as exc:
        _fail(f"row {row_num}: column {col} is not valid JSON: {exc}")


def _check_path(cell: str, row_num: int, col: int) -> None:
    if not Path(cell).expanduser().exists():
        _fail(f"row {row_num}: column {col} path does not exist: {cell}")


def validate_rows(
    file_path: Path,
    separator: str = "\t",
    selected_cols: Optional[Sequence[int]] = None,
    expect_columns: Optional[int] = None,
    allow_row_lens: Optional[Iterable[int]] = None,
    base64_cols: Optional[Sequence[int]] = None,
    image_cols: Optional[Sequence[int]] = None,
    int_seq_cols: Optional[Sequence[int]] = None,
    json_cols: Optional[Sequence[int]] = None,
    path_cols: Optional[Sequence[int]] = None,
    max_rows: Optional[int] = None,
) -> int:
    base64_cols = list(base64_cols or [])
    image_cols = list(image_cols or [])
    int_seq_cols = list(int_seq_cols or [])
    json_cols = list(json_cols or [])
    path_cols = list(path_cols or [])
    selected_cols = list(selected_cols or [])
    allow_row_lens = set(allow_row_lens or []) or None

    row_count = 0
    with file_path.open("r", encoding="utf-8") as handle:
        for row_num, raw_line in enumerate(handle, start=1):
            line = raw_line.rstrip("\n")
            if not line:
                _fail(f"row {row_num}: blank line encountered")
            columns = line.split(separator)
            row_len = len(columns)
            row_count += 1

            if expect_columns is not None and row_len != expect_columns:
                _fail(f"row {row_num}: expected {expect_columns} columns, found {row_len}")
            if allow_row_lens is not None and row_len not in allow_row_lens:
                _fail(f"row {row_num}: expected row length in {sorted(allow_row_lens)}, found {row_len}")
            for col in selected_cols:
                if col >= row_len:
                    _fail(f"row {row_num}: selected column {col} out of range for row length {row_len}")

            for col in base64_cols:
                _check_base64(columns[col], row_num, col)
            for col in image_cols:
                _check_image(columns[col], row_num, col)
            for col in int_seq_cols:
                _check_int_sequence(columns[col], row_num, col)
            for col in json_cols:
                _check_json(columns[col], row_num, col)
            for col in path_cols:
                _check_path(columns[col], row_num, col)

            if max_rows is not None and row_count >= max_rows:
                break

    if row_count == 0:
        _fail(f"{file_path}: file is empty")
    return row_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True, type=Path, help="TSV file to validate.")
    parser.add_argument("--separator", default="\t", help="Field separator, defaults to tab.")
    parser.add_argument("--selected-cols", default=None, help="Comma-separated selected column indices.")
    parser.add_argument("--expect-columns", type=int, default=None, help="Require this exact row width.")
    parser.add_argument(
        "--allow-row-lens",
        default=None,
        help="Comma-separated set of acceptable row widths, useful for mixed-layout TSVs.",
    )
    parser.add_argument("--base64-cols", default=None, help="Comma-separated columns to base64-decode.")
    parser.add_argument("--image-cols", default=None, help="Comma-separated columns to base64-decode and verify as images.")
    parser.add_argument("--int-seq-cols", default=None, help="Comma-separated columns containing integer sequences.")
    parser.add_argument("--json-cols", default=None, help="Comma-separated columns containing JSON strings.")
    parser.add_argument("--path-cols", default=None, help="Comma-separated columns that should exist as filesystem paths.")
    parser.add_argument("--max-rows", type=int, default=None, help="Stop after this many rows.")
    args = parser.parse_args()

    try:
        row_count = validate_rows(
            args.file,
            separator=args.separator,
            selected_cols=parse_col_list(args.selected_cols),
            expect_columns=args.expect_columns,
            allow_row_lens=parse_int_set(args.allow_row_lens),
            base64_cols=parse_col_list(args.base64_cols),
            image_cols=parse_col_list(args.image_cols),
            int_seq_cols=parse_col_list(args.int_seq_cols),
            json_cols=parse_col_list(args.json_cols),
            path_cols=parse_col_list(args.path_cols),
            max_rows=args.max_rows,
        )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"validated {row_count} rows in {args.file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
