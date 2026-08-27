#!/usr/bin/env python3
"""Prune Anserini-style SPLADE document JSONL by per-token value quantile.

The script computes a threshold for each token from observed values across the
input collection, then keeps token occurrences whose value is strictly greater
than that token's threshold.
"""

from __future__ import annotations

import argparse
import fnmatch
import gzip
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, DefaultDict, Dict, Iterator, List, Mapping, Optional, Tuple

JsonRecord = Dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prune SPLADE/Anserini document JSONL vectors by per-token quantile thresholds."
    )
    parser.add_argument("--input-dir", required=True, type=Path, help="Directory containing .jsonl or .jsonl.gz files.")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory for quantile-pruned JSONL output files.")
    parser.add_argument("--quantile", type=float, required=True, help="Quantile in [0, 1] used as each token's threshold.")
    parser.add_argument(
        "--include",
        action="append",
        default=None,
        help="Glob pattern for input filenames. May be repeated. Defaults to *.jsonl and *.jsonl.gz.",
    )
    parser.add_argument("--limit", type=int, default=0, help="Process at most N records across all files; 0 means no limit.")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and report thresholds without writing files.")
    parser.add_argument("--overwrite", action="store_true", help="Allow writing into an existing non-empty output directory.")
    parser.add_argument(
        "--print-thresholds",
        action="store_true",
        help="Print per-token thresholds as JSON to stdout after the scan.",
    )
    return parser.parse_args()


def open_text(path: Path, mode: str):
    if path.name.endswith(".gz"):
        return gzip.open(path, mode, encoding="utf-8")
    return path.open(mode, encoding="utf-8")


def discover_files(input_dir: Path, patterns: List[str]) -> List[Path]:
    files = [path for path in sorted(input_dir.iterdir()) if path.is_file() and any(fnmatch.fnmatch(path.name, p) for p in patterns)]
    if not files:
        joined = ", ".join(patterns)
        raise ValueError(f"no input files matched {joined!r} in {input_dir}")
    return files


def validate_args(args: argparse.Namespace) -> List[str]:
    if not args.input_dir.is_dir():
        raise ValueError(f"--input-dir is not a directory: {args.input_dir}")
    if args.output_dir.resolve() == args.input_dir.resolve():
        raise ValueError("--output-dir must not be the same directory as --input-dir")
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite and not args.dry_run:
        raise ValueError(f"output directory exists and is not empty: {args.output_dir}; use --overwrite to allow it")
    if not 0.0 <= args.quantile <= 1.0:
        raise ValueError("--quantile must be between 0 and 1")
    if args.limit < 0:
        raise ValueError("--limit must be non-negative")
    return args.include or ["*.jsonl", "*.jsonl.gz"]


def validate_record(record: Any, source: Path, line_no: int) -> JsonRecord:
    if not isinstance(record, dict):
        raise ValueError(f"{source}:{line_no}: record is not a JSON object")
    if "vector" not in record:
        raise ValueError(f"{source}:{line_no}: missing 'vector' field")
    if not isinstance(record["vector"], dict):
        raise ValueError(f"{source}:{line_no}: 'vector' must be an object")
    for token, value in record["vector"].items():
        if not isinstance(token, str):
            raise ValueError(f"{source}:{line_no}: vector token keys must be strings")
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"{source}:{line_no}: vector value for {token!r} is not numeric")
    return record


def iter_records(path: Path) -> Iterator[Tuple[int, JsonRecord]]:
    with open_text(path, "rt") as reader:
        for line_no, line in enumerate(reader, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            yield line_no, validate_record(record, path, line_no)


def bounded_records(files: List[Path], limit: int) -> Iterator[Tuple[Path, int, JsonRecord]]:
    seen = 0
    for path in files:
        for line_no, record in iter_records(path):
            if limit and seen >= limit:
                return
            seen += 1
            yield path, line_no, record


def quantile(values: List[float], q: float) -> float:
    if not values:
        raise ValueError("cannot compute quantile of empty values")
    sorted_values = sorted(values)
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[int(position)]
    fraction = position - lower
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * fraction


def collect_values(files: List[Path], limit: int) -> Tuple[DefaultDict[str, List[float]], int]:
    values: DefaultDict[str, List[float]] = defaultdict(list)
    count = 0
    for _, _, record in bounded_records(files, limit):
        for token, value in record["vector"].items():
            values[token].append(float(value))
        count += 1
    return values, count


def prune_record(record: Mapping[str, Any], thresholds: Mapping[str, float]) -> JsonRecord:
    pruned = dict(record)
    pruned["vector"] = {token: value for token, value in record["vector"].items() if value > thresholds[token]}
    return pruned


def write_record(writer, record: Mapping[str, Any]) -> None:
    writer.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def write_outputs(files: List[Path], output_dir: Path, thresholds: Mapping[str, float], limit: int) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    writers = {}
    total = 0
    try:
        for path in files:
            writer = open_text(output_dir / path.name, "wt")
            writers[path] = writer
            for _, record in iter_records(path):
                if limit and total >= limit:
                    return total
                write_record(writer, prune_record(record, thresholds))
                total += 1
    finally:
        for writer in writers.values():
            writer.close()
    return total


def main() -> int:
    args = parse_args()
    try:
        patterns = validate_args(args)
        files = discover_files(args.input_dir, patterns)
        values, scanned = collect_values(files, args.limit)
        if not values:
            raise ValueError("no vector values found in input records")
        thresholds = {token: quantile(token_values, args.quantile) for token, token_values in sorted(values.items())}

        print(f"input files: {len(files)}")
        print(f"records scanned: {scanned}")
        print(f"tokens with thresholds: {len(thresholds)}")
        print(f"quantile: {args.quantile}")
        if args.print_thresholds:
            print(json.dumps(thresholds, ensure_ascii=False, sort_keys=True))
        if args.dry_run:
            print("dry run: no files will be written")
            return 0

        written = write_outputs(files, args.output_dir, thresholds, args.limit)
        print(f"records written: {written}")
        print(f"output directory: {args.output_dir}")
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
