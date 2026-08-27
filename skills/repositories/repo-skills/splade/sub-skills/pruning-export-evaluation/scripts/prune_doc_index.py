#!/usr/bin/env python3
"""Prune Anserini-style SPLADE document JSONL by top-k size or value.

Input records must be JSON objects with a ``vector`` mapping. The script keeps
all non-vector fields unchanged and writes JSONL files with the same filenames
as the input files.
"""

from __future__ import annotations

import argparse
import fnmatch
import gzip
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Tuple

JsonRecord = Dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prune SPLADE/Anserini document JSONL vectors by top-k size and/or value threshold."
    )
    parser.add_argument("--input-dir", required=True, type=Path, help="Directory containing .jsonl or .jsonl.gz files.")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory for pruned JSONL output files.")
    parser.add_argument("--top-k", type=int, default=0, help="Keep only the highest weighted K tokens per document.")
    parser.add_argument(
        "--value-to-prune",
        type=float,
        default=0.0,
        help="Keep tokens with value strictly greater than value_to_prune * value_scale.",
    )
    parser.add_argument(
        "--value-scale",
        type=float,
        default=100.0,
        help="Scale applied to --value-to-prune. Default 100 mirrors SPLADE's original pruning script.",
    )
    parser.add_argument(
        "--include",
        action="append",
        default=None,
        help="Glob pattern for input filenames. May be repeated. Defaults to *.jsonl and *.jsonl.gz.",
    )
    parser.add_argument("--limit", type=int, default=0, help="Process at most N records across all files; 0 means no limit.")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and report planned outputs without writing files.")
    parser.add_argument("--overwrite", action="store_true", help="Allow writing into existing non-empty output directories.")
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
    if args.top_k < 0:
        raise ValueError("--top-k must be non-negative")
    if args.value_to_prune < 0:
        raise ValueError("--value-to-prune must be non-negative")
    if args.value_scale <= 0:
        raise ValueError("--value-scale must be positive")
    if args.limit < 0:
        raise ValueError("--limit must be non-negative")
    if args.top_k == 0 and args.value_to_prune == 0:
        raise ValueError("choose at least one pruning mode: --top-k or --value-to-prune")
    return args.include or ["*.jsonl", "*.jsonl.gz"]


def ensure_output_dir(path: Path, input_dir: Path, overwrite: bool, dry_run: bool) -> None:
    if path.resolve() == input_dir.resolve():
        raise ValueError("output target must not be the same directory as --input-dir")
    if dry_run:
        return
    if path.exists() and any(path.iterdir()) and not overwrite:
        raise ValueError(f"output directory exists and is not empty: {path}; use --overwrite to allow it")
    path.mkdir(parents=True, exist_ok=True)


def output_targets(base_output_dir: Path, args: argparse.Namespace) -> List[Tuple[str, Path]]:
    modes: List[Tuple[str, Path]] = []
    enabled = int(args.top_k > 0) + int(args.value_to_prune > 0)
    if args.top_k > 0:
        target = base_output_dir if enabled == 1 else base_output_dir / f"prune_size_{args.top_k}"
        modes.append(("top_k", target))
    if args.value_to_prune > 0:
        label = str(args.value_to_prune).replace("/", "_")
        target = base_output_dir if enabled == 1 else base_output_dir / f"prune_value_{label}"
        modes.append(("value", target))
    return modes


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


def prune_by_top_k(record: Mapping[str, Any], top_k: int) -> JsonRecord:
    pruned = dict(record)
    items = sorted(record["vector"].items(), key=lambda item: item[1], reverse=True)[:top_k]
    pruned["vector"] = {token: value for token, value in items}
    return pruned


def prune_by_value(record: Mapping[str, Any], threshold: float) -> JsonRecord:
    pruned = dict(record)
    pruned["vector"] = {token: value for token, value in record["vector"].items() if value > threshold}
    return pruned


def write_record(writer, record: Mapping[str, Any]) -> None:
    writer.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def process_file(path: Path, targets: List[Tuple[str, Path]], args: argparse.Namespace, remaining: Optional[int]) -> int:
    writers = {}
    written = 0
    try:
        if not args.dry_run:
            for mode, target_dir in targets:
                writers[mode] = open_text(target_dir / path.name, "wt")
        for _, record in iter_records(path):
            if remaining is not None and written >= remaining:
                break
            if "top_k" in writers or args.dry_run:
                top_record = prune_by_top_k(record, args.top_k) if args.top_k > 0 else None
                if not args.dry_run and top_record is not None:
                    write_record(writers["top_k"], top_record)
            if "value" in writers or args.dry_run:
                value_record = prune_by_value(record, args.value_to_prune * args.value_scale) if args.value_to_prune > 0 else None
                if not args.dry_run and value_record is not None:
                    write_record(writers["value"], value_record)
            written += 1
    finally:
        for writer in writers.values():
            writer.close()
    return written


def main() -> int:
    args = parse_args()
    try:
        patterns = validate_args(args)
        files = discover_files(args.input_dir, patterns)
        targets = output_targets(args.output_dir, args)
        for _, target_dir in targets:
            ensure_output_dir(target_dir, args.input_dir, args.overwrite, args.dry_run)

        print(f"input files: {len(files)}")
        for mode, target_dir in targets:
            if mode == "top_k":
                print(f"top-k pruning: keep {args.top_k} tokens -> {target_dir}")
            else:
                print(f"value pruning: keep value > {args.value_to_prune * args.value_scale:g} -> {target_dir}")
        if args.dry_run:
            print("dry run: no files will be written")

        total = 0
        for path in files:
            remaining = None if args.limit == 0 else max(args.limit - total, 0)
            if remaining == 0:
                break
            count = process_file(path, targets, args, remaining)
            total += count
            print(f"processed {count} records from {path.name}")
        print(f"total records processed: {total}")
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI should report validation errors cleanly.
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
