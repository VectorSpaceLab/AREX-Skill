#!/usr/bin/env python3
"""Validate an OpenCLIP CSV/TSV image-text dataset without training.

This helper mirrors the safety-relevant behavior of OpenCLIP's CsvDataset:
- verifies the image path and caption columns exist,
- stringifies caption values for the numeric-caption warning,
- optionally checks image path existence,
- never imports OpenCLIP, constructs models, tokenizes text, or starts training.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import Iterable


_SEPARATOR_ALIASES = {
    "tab": "\t",
    "\\t": "\t",
    "t": "\t",
    "comma": ",",
    ",": ",",
    "semicolon": ";",
    ";": ";",
    "pipe": "|",
    "|": "|",
    "space": " ",
}


def _separator(value: str) -> str:
    if value in _SEPARATOR_ALIASES:
        return _SEPARATOR_ALIASES[value]
    if len(value) == 1:
        return value
    raise argparse.ArgumentTypeError(
        "separator must be one character or one of: tab, comma, semicolon, pipe, space"
    )


def _is_numeric_like(value: str) -> bool:
    value = value.strip()
    if not value:
        return False
    try:
        float(value)
    except ValueError:
        return False
    return True


def _preview(values: Iterable[str], limit: int = 5) -> str:
    shown = list(values)[:limit]
    suffix = "" if len(shown) < limit else ", ..."
    return ", ".join(repr(v) for v in shown) + suffix


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", help="CSV/TSV file to validate.")
    parser.add_argument("--image-key", "--csv-img-key", default="filepath", help="Image path column name.")
    parser.add_argument("--caption-key", "--csv-caption-key", default="title", help="Caption column name.")
    parser.add_argument(
        "--separator",
        "--csv-separator",
        default="tab",
        type=_separator,
        help="Column separator. Use tab, comma, semicolon, pipe, space, or a literal one-character separator.",
    )
    parser.add_argument(
        "--base-dir",
        default=None,
        help="Base directory for relative image paths. Defaults to the current working directory, matching OpenCLIP's Image.open behavior.",
    )
    parser.add_argument(
        "--no-check-images",
        action="store_true",
        help="Skip image path existence checks; still validate columns and captions.",
    )
    parser.add_argument(
        "--max-missing",
        type=int,
        default=20,
        help="Maximum missing image paths to print before summarizing.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Validate only the first N data rows after the header.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    csv_path = Path(args.csv_path)
    if not csv_path.is_file():
        print(f"ERROR: dataset file does not exist: {csv_path}", file=sys.stderr)
        return 2

    base_dir = Path(args.base_dir) if args.base_dir else Path.cwd()
    row_count = 0
    empty_image_rows: list[int] = []
    empty_caption_rows: list[int] = []
    missing_images: list[tuple[int, str]] = []
    numeric_caption_rows: list[tuple[int, str]] = []

    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=args.separator)
            fieldnames = reader.fieldnames or []
            missing_columns = [
                key for key in (args.image_key, args.caption_key)
                if key not in fieldnames
            ]
            if missing_columns:
                print("ERROR: required column(s) missing: " + ", ".join(missing_columns), file=sys.stderr)
                print("Available columns: " + _preview(fieldnames), file=sys.stderr)
                if len(fieldnames) == 1 and args.separator != ",":
                    print("Hint: the separator may be wrong; try --separator comma or inspect the header.", file=sys.stderr)
                elif len(fieldnames) == 1 and args.separator == ",":
                    print("Hint: the separator may be wrong; OpenCLIP defaults to tab for CSV-like datasets.", file=sys.stderr)
                return 2

            for row_index, row in enumerate(reader, start=2):
                if args.max_rows is not None and row_count >= args.max_rows:
                    break
                row_count += 1
                image_value = (row.get(args.image_key) or "").strip()
                caption_raw = row.get(args.caption_key)
                caption_value = "" if caption_raw is None else str(caption_raw)

                if not image_value:
                    empty_image_rows.append(row_index)
                elif not args.no_check_images:
                    image_path = Path(image_value)
                    if not image_path.is_absolute():
                        image_path = base_dir / image_path
                    if not image_path.is_file():
                        missing_images.append((row_index, image_value))

                if not caption_value.strip():
                    empty_caption_rows.append(row_index)
                elif _is_numeric_like(caption_value):
                    numeric_caption_rows.append((row_index, caption_value))
    except UnicodeDecodeError as exc:
        print(f"ERROR: could not decode file as UTF-8: {exc}", file=sys.stderr)
        return 2
    except csv.Error as exc:
        print(f"ERROR: CSV parsing failed: {exc}", file=sys.stderr)
        return 2

    print("OpenCLIP CSV dataset validation")
    print(f"  file: {csv_path}")
    print(f"  separator: {repr(args.separator)}")
    print(f"  image key: {args.image_key}")
    print(f"  caption key: {args.caption_key}")
    print(f"  rows checked: {row_count}")
    print(f"  image existence checks: {'skipped' if args.no_check_images else 'enabled'}")

    errors = 0
    if row_count == 0:
        print("ERROR: no data rows found", file=sys.stderr)
        errors += 1
    if empty_image_rows:
        print(f"ERROR: empty image values at rows: {_preview(map(str, empty_image_rows))}", file=sys.stderr)
        errors += 1
    if empty_caption_rows:
        print(f"ERROR: empty captions at rows: {_preview(map(str, empty_caption_rows))}", file=sys.stderr)
        errors += 1
    if missing_images:
        errors += 1
        print(f"ERROR: missing image files: {len(missing_images)}", file=sys.stderr)
        for row_index, image_value in missing_images[:max(0, args.max_missing)]:
            print(f"  row {row_index}: {image_value}", file=sys.stderr)
        if len(missing_images) > args.max_missing:
            print(f"  ... {len(missing_images) - args.max_missing} more", file=sys.stderr)

    if numeric_caption_rows:
        print(
            "NOTE: numeric-looking captions found; OpenCLIP stringifies captions before tokenization. "
            "Verify that this is the intended caption column."
        )
        for row_index, caption_value in numeric_caption_rows[:5]:
            print(f"  row {row_index}: {caption_value!r} -> {str(caption_value)!r}")
        if len(numeric_caption_rows) > 5:
            print(f"  ... {len(numeric_caption_rows) - 5} more numeric-looking captions")

    if errors:
        return 1
    print("OK: required columns and checked paths look valid for OpenCLIP CsvDataset.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
