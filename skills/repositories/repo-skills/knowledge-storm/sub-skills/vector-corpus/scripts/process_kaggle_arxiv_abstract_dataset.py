#!/usr/bin/env python3
"""Convert Kaggle arXiv abstracts CSVs into VectorRM-compatible CSVs.

Expected default input is Kaggle arxiv_data_210930-054931.csv with columns:
terms, abstracts, titles. The output always has columns:
content, title, url, description.

This helper intentionally uses only the Python standard library so --help works
from any working directory before installing pandas, STORM, Qdrant, or embedding
dependencies.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

OUTPUT_COLUMNS = ("content", "title", "url", "description")


def _is_blank(value: object) -> bool:
    return value is None or str(value).strip() == ""


def _open_dict_reader(input_path: Path) -> tuple[csv.DictReader, object]:
    handle = input_path.open("r", encoding="utf-8-sig", newline="")
    return csv.DictReader(handle), handle


def convert_dataset(args: argparse.Namespace) -> int:
    input_path: Path = args.input_path
    output_path: Path = args.output_path

    if input_path.suffix.lower() != ".csv":
        print(f"ERROR: input path must end with .csv: {input_path}", file=sys.stderr)
        return 1
    if not input_path.exists() or not input_path.is_file():
        print(f"ERROR: input path does not exist or is not a file: {input_path}", file=sys.stderr)
        return 1
    if input_path.resolve() == output_path.resolve(strict=False):
        print("ERROR: output path must be different from input path.", file=sys.stderr)
        return 1

    try:
        reader, handle = _open_dict_reader(input_path)
    except OSError as exc:
        print(f"ERROR: unable to read input CSV: {exc}", file=sys.stderr)
        return 1

    with handle:
        if reader.fieldnames is None:
            print("ERROR: CSV has no header row.", file=sys.stderr)
            return 1
        headers = [h.strip() if h is not None else "" for h in reader.fieldnames]
        required_columns = [args.abstract_column, args.title_column]
        if not args.no_filter:
            required_columns.append(args.terms_column)
        missing = [column for column in required_columns if column not in headers]
        if missing:
            print(
                "ERROR: missing required input column(s): " + ", ".join(missing),
                file=sys.stderr,
            )
            return 1

        output_rows: list[dict[str, str]] = []
        original_count = 0
        filtered_out = 0
        dropped_empty = 0

        try:
            for row in reader:
                original_count += 1
                if not args.no_filter and row.get(args.terms_column) != args.filter_term:
                    filtered_out += 1
                    continue

                content = "" if row.get(args.abstract_column) is None else str(row.get(args.abstract_column)).strip()
                title = "" if row.get(args.title_column) is None else str(row.get(args.title_column)).strip()
                if _is_blank(content):
                    dropped_empty += 1
                    continue

                output_rows.append(
                    {
                        "content": content,
                        "title": title,
                        "url": f"{args.url_prefix}{len(output_rows)}",
                        "description": args.description,
                    }
                )
        except csv.Error as exc:
            print(f"ERROR: unable to parse input CSV: {exc}", file=sys.stderr)
            return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader()
            writer.writerows(output_rows)
    except OSError as exc:
        print(f"ERROR: unable to write output CSV: {exc}", file=sys.stderr)
        return 1

    print(f"Read {original_count} input row(s).")
    if args.no_filter:
        print("Filter disabled; considered all rows.")
    else:
        print(
            f"Filtered out {filtered_out} row(s) where {args.terms_column} != {args.filter_term!r}."
        )
    print(f"Dropped {dropped_empty} selected row(s) with empty {args.abstract_column}.")
    print(f"Wrote {len(output_rows)} VectorRM row(s) to {output_path}.")
    print("Output columns: " + ", ".join(OUTPUT_COLUMNS))

    if not output_rows:
        print(
            "WARNING: output CSV has zero data rows; check --filter-term or use --no-filter.",
            file=sys.stderr,
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert Kaggle arXiv abstracts data to a VectorRM-compatible CSV "
            "with content,title,url,description columns."
        )
    )
    parser.add_argument(
        "--input-path",
        required=True,
        type=Path,
        help="Path to Kaggle arxiv_data_210930-054931.csv or a compatible CSV.",
    )
    parser.add_argument(
        "--output-path",
        required=True,
        type=Path,
        help="Path to write the VectorRM-compatible CSV.",
    )
    parser.add_argument(
        "--terms-column",
        default="terms",
        help="Input column containing arXiv category terms. Default: terms.",
    )
    parser.add_argument(
        "--abstract-column",
        default="abstracts",
        help="Input column containing document text. Default: abstracts.",
    )
    parser.add_argument(
        "--title-column",
        default="titles",
        help="Input column containing document titles. Default: titles.",
    )
    parser.add_argument(
        "--filter-term",
        default="['cs.CV']",
        help="Keep rows whose terms column exactly equals this value. Default: ['cs.CV'].",
    )
    parser.add_argument(
        "--no-filter",
        action="store_true",
        help="Disable terms filtering and convert all rows with non-empty abstracts.",
    )
    parser.add_argument(
        "--url-prefix",
        default="uid_",
        help="Prefix for synthetic unique url identifiers. Default: uid_.",
    )
    parser.add_argument(
        "--description",
        default="",
        help="Constant description value to write for every output row. Default: empty string.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return convert_dataset(args)


if __name__ == "__main__":
    raise SystemExit(main())
