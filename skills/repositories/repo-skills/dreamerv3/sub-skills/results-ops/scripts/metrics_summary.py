#!/usr/bin/env python3
"""Summarize DreamerV3 JSONL metrics and gzip score-record files.

Supports:
  * metrics.jsonl / scores.jsonl records: {"step": ..., "episode/score": ...}
  * *.json.gz score records: [{"task": ..., "method": ..., "seed": ..., "xs": [...], "ys": [...]}]

The script intentionally uses only Python standard-library modules.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import pathlib
import statistics
import sys
from typing import Any, Dict, Iterable, Iterator, List, Sequence, Tuple


JSONRecord = Dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "List keys or summarize DreamerV3 metrics.jsonl, scores.jsonl, "
            "or gzipped score-record JSON files."
        )
    )
    parser.add_argument(
        "--input",
        nargs="+",
        required=True,
        help=(
            "One or more files/directories. Directories are searched for "
            "metrics.jsonl, scores.jsonl, and *.json.gz."
        ),
    )
    parser.add_argument(
        "--key",
        default="episode/score",
        help=(
            "Metric key to summarize. For gzip score records, aliases "
            "episode/score and score map to ys; step maps to xs."
        ),
    )
    parser.add_argument(
        "--last",
        type=int,
        default=10,
        help="Number of most recent finite values used for the recent mean.",
    )
    parser.add_argument(
        "--list-keys",
        action="store_true",
        help="List available keys/aliases instead of summarizing values.",
    )
    return parser.parse_args()


def discover(inputs: Sequence[str]) -> List[pathlib.Path]:
    files: List[pathlib.Path] = []
    seen = set()
    for raw in inputs:
        path = pathlib.Path(raw).expanduser()
        if not path.exists():
            raise FileNotFoundError(path)
        candidates: Iterable[pathlib.Path]
        if path.is_dir():
            candidates = sorted(
                list(path.rglob("metrics.jsonl"))
                + list(path.rglob("scores.jsonl"))
                + list(path.rglob("*.json.gz"))
            )
        else:
            candidates = [path]
        for candidate in candidates:
            key = candidate.resolve()
            if key not in seen:
                seen.add(key)
                files.append(candidate)
    return files


def open_text(path: pathlib.Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("rt", encoding="utf-8")


def load_jsonl(path: pathlib.Path) -> Tuple[List[JSONRecord], int]:
    records: List[JSONRecord] = []
    errors = 0
    with open_text(path) as handle:
        for lineno, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                errors += 1
                continue
            if isinstance(value, dict):
                records.append(value)
            else:
                print(
                    f"warning: {path}:{lineno}: expected JSON object, got "
                    f"{type(value).__name__}",
                    file=sys.stderr,
                )
                errors += 1
    return records, errors


def load_json_records(path: pathlib.Path) -> Tuple[List[JSONRecord], int]:
    try:
        with open_text(path) as handle:
            value = json.load(handle)
    except json.JSONDecodeError:
        # Some users gzip JSONL files. Fall back to JSONL parsing.
        return load_jsonl(path)
    if isinstance(value, list):
        records = [x for x in value if isinstance(x, dict)]
        return records, len(value) - len(records)
    if isinstance(value, dict):
        return [value], 0
    return [], 1


def is_score_record(record: JSONRecord) -> bool:
    return (
        isinstance(record.get("xs"), list)
        and isinstance(record.get("ys"), list)
        and "task" in record
        and "method" in record
    )


def load_records(path: pathlib.Path) -> Tuple[str, List[JSONRecord], int]:
    if path.name.endswith(".jsonl"):
        records, errors = load_jsonl(path)
        return "jsonl", records, errors
    records, errors = load_json_records(path)
    kind = "score-json" if records and is_score_record(records[0]) else "json"
    return kind, records, errors


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def finite(value: Any) -> bool:
    return is_number(value) and math.isfinite(float(value))


def fmt(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            return "NA"
        if value.is_integer():
            return str(int(value))
        return f"{value:.6g}"
    return str(value)


def key_alias_for_score_records(key: str) -> str:
    normalized = key.strip()
    if normalized in {"episode/score", "score", "ys", "return", "reward"}:
        return "ys"
    if normalized in {"step", "steps", "x", "xs", "budget"}:
        return "xs"
    return normalized


def list_keys(path: pathlib.Path, kind: str, records: Sequence[JSONRecord], errors: int) -> None:
    keys = set()
    score = any(is_score_record(x) for x in records)
    for record in records:
        keys.update(record.keys())
    aliases = []
    if score:
        aliases = ["episode/score->ys", "score->ys", "step->xs", "budget->xs"]
    print(f"# {path} ({kind}, records={len(records)}, parse_errors={errors})")
    if keys:
        print("keys\t" + "\t".join(sorted(keys)))
    else:
        print("keys\t")
    if aliases:
        print("aliases\t" + "\t".join(aliases))


def pairs_from_jsonl(records: Sequence[JSONRecord], key: str) -> List[Tuple[Any, float]]:
    pairs: List[Tuple[Any, float]] = []
    for index, record in enumerate(records):
        if key not in record:
            continue
        value = record[key]
        if not finite(value):
            continue
        step = record.get("step", index)
        pairs.append((step, float(value)))
    return pairs


def pairs_from_score_record(record: JSONRecord, key: str) -> List[Tuple[Any, float]]:
    actual = key_alias_for_score_records(key)
    values = record.get(actual)
    if values is None:
        return []
    if not isinstance(values, list):
        values = [values]
    xs = record.get("xs")
    if isinstance(xs, list) and actual != "xs":
        steps = xs
    else:
        steps = list(range(len(values)))
    pairs: List[Tuple[Any, float]] = []
    for index, value in enumerate(values):
        if finite(value):
            step = steps[index] if index < len(steps) else index
            pairs.append((step, float(value)))
    return pairs


def summarize_pairs(
    path: pathlib.Path,
    kind: str,
    group: str,
    key: str,
    pairs: Sequence[Tuple[Any, float]],
    last: int,
    errors: int,
) -> str | None:
    if not pairs:
        return None
    recent_values = [value for _, value in pairs[-max(1, last) :]]
    all_values = [value for _, value in pairs]
    row = [
        str(path),
        kind,
        group,
        key,
        str(len(pairs)),
        fmt(pairs[0][0]),
        fmt(pairs[-1][0]),
        fmt(pairs[-1][1]),
        fmt(statistics.fmean(recent_values)),
        fmt(min(all_values)),
        fmt(max(all_values)),
        str(errors),
    ]
    return "\t".join(row)


def summarize_file(path: pathlib.Path, key: str, last: int) -> List[str]:
    kind, records, errors = load_records(path)
    rows: List[str] = []
    if kind == "score-json" or any(is_score_record(x) for x in records):
        for record in records:
            if not is_score_record(record):
                continue
            group = "/".join(
                str(record.get(name, "?")) for name in ("task", "method", "seed")
            )
            row = summarize_pairs(
                path,
                "score-json",
                group,
                key,
                pairs_from_score_record(record, key),
                last,
                errors,
            )
            if row:
                rows.append(row)
    else:
        row = summarize_pairs(
            path,
            kind,
            "-",
            key,
            pairs_from_jsonl(records, key),
            last,
            errors,
        )
        if row:
            rows.append(row)
    return rows


def main() -> int:
    args = parse_args()
    if args.last < 1:
        print("error: --last must be >= 1", file=sys.stderr)
        return 2
    try:
        files = discover(args.input)
    except FileNotFoundError as exc:
        print(f"error: input not found: {exc}", file=sys.stderr)
        return 2
    if not files:
        print("error: no input files found", file=sys.stderr)
        return 2

    if args.list_keys:
        for path in files:
            kind, records, errors = load_records(path)
            list_keys(path, kind, records, errors)
        return 0

    print(
        "file\tkind\tgroup\tkey\tcount\tfirst_step\tlast_step\tlast_value"
        "\trecent_mean\tmin\tmax\tparse_errors"
    )
    rows: List[str] = []
    for path in files:
        rows.extend(summarize_file(path, args.key, args.last))
    for row in rows:
        print(row)
    if not rows:
        print(
            f"warning: no finite values found for key {args.key!r}; use --list-keys",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
