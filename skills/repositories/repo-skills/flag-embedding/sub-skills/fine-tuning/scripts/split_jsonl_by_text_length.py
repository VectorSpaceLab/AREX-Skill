#!/usr/bin/env python3
"""Split FlagEmbedding training JSONL by safe text length estimates."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from pathlib import Path
from typing import Any, Iterable


TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def iter_json_files(input_path: Path) -> list[Path]:
    if input_path.is_dir():
        return sorted(p for p in input_path.iterdir() if p.suffix in {".json", ".jsonl"} and p.is_file())
    return [input_path]


def validate_length_list(values: list[int]) -> list[int]:
    if not values:
        raise ValueError("length-list must not be empty")
    values = sorted(set(values))
    if values[0] < 0:
        raise ValueError("length-list values must be non-negative")
    return values


def ranges_from_bounds(bounds: list[int]) -> list[tuple[int, float]]:
    ranges: list[tuple[int, float]] = []
    for index, left in enumerate(bounds):
        right = bounds[index + 1] if index + 1 < len(bounds) else math.inf
        if not left < right:
            raise ValueError("length-list values must be strictly increasing after deduplication")
        ranges.append((left, right))
    return ranges


def text_values(record: dict[str, Any], include_prompt: bool) -> Iterable[str]:
    value = record.get("query")
    if isinstance(value, str):
        yield value
    for key in ("pos", "neg"):
        value = record.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    yield item
    if include_prompt:
        for key in ("prompt", "query_prompt", "passage_prompt"):
            value = record.get(key)
            if isinstance(value, str):
                yield value


def estimate_text_length(text: str, mode: str, chars_per_token: float) -> int:
    if mode == "chars":
        return len(text)
    if mode == "token-estimate":
        regex_count = len(TOKEN_RE.findall(text))
        char_estimate = math.ceil(len(text) / chars_per_token) if text else 0
        return max(regex_count, char_estimate)
    raise ValueError(f"unknown length mode: {mode}")


def record_length(record: dict[str, Any], mode: str, chars_per_token: float, include_prompt: bool) -> int:
    lengths = [estimate_text_length(text, mode, chars_per_token) for text in text_values(record, include_prompt)]
    return max(lengths) if lengths else 0


def bucket_name(left: int, right: float) -> str:
    if math.isinf(right):
        return f"len-{left}-plus"
    return f"len-{left}-{int(right)}"


def bucket_for_length(length: int, ranges: list[tuple[int, float]]) -> tuple[int, float]:
    for left, right in ranges:
        if left <= length < right:
            return left, right
    return ranges[-1]


def open_outputs(input_file: Path, output_dir: Path, ranges: list[tuple[int, float]], overwrite: bool):
    handles = {}
    stem = input_file.stem
    for left, right in ranges:
        output_path = output_dir / f"{stem}_{bucket_name(left, right)}.jsonl"
        if output_path.exists() and not overwrite:
            raise FileExistsError(f"{output_path} exists; pass --overwrite to replace it")
        handles[(left, right)] = output_path.open("w", encoding="utf-8")
    return handles


def process_file(
    input_file: Path,
    output_dir: Path,
    ranges: list[tuple[int, float]],
    mode: str,
    chars_per_token: float,
    include_prompt: bool,
    overwrite: bool,
) -> dict[str, Any]:
    if not input_file.exists() or not input_file.is_file():
        raise FileNotFoundError(f"input file not found: {input_file}")

    counts = {bucket_name(left, right): 0 for left, right in ranges}
    lengths: list[int] = []
    started_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    handles = open_outputs(input_file, output_dir, ranges, overwrite)
    try:
        with input_file.open("r", encoding="utf-8") as reader:
            for line_number, line in enumerate(reader, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{input_file}:{line_number}: invalid JSON: {exc}") from exc
                if not isinstance(record, dict):
                    raise ValueError(f"{input_file}:{line_number}: line must be a JSON object")
                length = record_length(record, mode, chars_per_token, include_prompt)
                bucket = bucket_for_length(length, ranges)
                handles[bucket].write(json.dumps(record, ensure_ascii=False) + "\n")
                counts[bucket_name(*bucket)] += 1
                lengths.append(length)
    finally:
        for handle in handles.values():
            handle.close()

    ended_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    return {
        "file_name": input_file.name,
        "records": len(lengths),
        "length_mode": mode,
        "avg_length": (sum(lengths) / len(lengths)) if lengths else 0,
        "max_length": max(lengths) if lengths else 0,
        "started_at": started_at,
        "ended_at": ended_at,
        "split_info": counts,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-path", required=True, help="Input JSONL file or directory of .json/.jsonl files")
    parser.add_argument("--output-dir", required=True, help="Directory where split JSONL files are written")
    parser.add_argument(
        "--length-list",
        nargs="+",
        type=int,
        default=[0, 500, 1000, 2000, 3000, 4000, 5000, 6000, 7000],
        help="Lower bounds for output buckets; the final bucket is open-ended",
    )
    parser.add_argument(
        "--length-mode",
        choices=["chars", "token-estimate"],
        default="token-estimate",
        help="Use raw character length or an offline token estimate",
    )
    parser.add_argument(
        "--chars-per-token",
        type=float,
        default=4.0,
        help="Character divisor used by token-estimate mode",
    )
    parser.add_argument("--include-prompt", action="store_true", help="Include prompt/query_prompt/passage_prompt in length estimates")
    parser.add_argument("--log-name", default=".split_log.jsonl", help="Log file name written inside output-dir")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing split output files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.chars_per_token <= 0:
        print("ERROR: --chars-per-token must be positive", file=sys.stderr)
        return 1
    try:
        bounds = validate_length_list(args.length_list)
        ranges = ranges_from_bounds(bounds)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    input_path = Path(args.input_path)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    files = iter_json_files(input_path)
    if not files:
        print("ERROR: no .json or .jsonl files found", file=sys.stderr)
        return 1

    log_path = output_dir / args.log_name
    try:
        with log_path.open("a", encoding="utf-8") as log_file:
            for input_file in files:
                info = process_file(
                    input_file=input_file,
                    output_dir=output_dir,
                    ranges=ranges,
                    mode=args.length_mode,
                    chars_per_token=args.chars_per_token,
                    include_prompt=args.include_prompt,
                    overwrite=args.overwrite,
                )
                log_file.write(json.dumps(info, ensure_ascii=False) + "\n")
                print(f"split {input_file}: records={info['records']} max_length={info['max_length']}", file=sys.stderr)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
