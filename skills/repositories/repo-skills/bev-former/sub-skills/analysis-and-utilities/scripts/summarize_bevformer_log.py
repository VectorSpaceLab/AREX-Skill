#!/usr/bin/env python3
"""Summarize BEVFormer JSON or JSONL logs without repo imports.

Purpose:
- inspect one or more log files
- report loss, lr, and a user-chosen metric
- tolerate JSONL, JSON arrays, and stray non-JSON lines

Prerequisites:
- Python 3.8+
- log files already on disk

Example:
  python summarize_bevformer_log.py work_dirs/run.jsonl --metric NDS
"""

import argparse
import json
import math
import sys
from pathlib import Path

SEPARATORS = "/_:-."
PREFERRED_AXIS_KEYS = ("epoch", "iter", "step", "global_step")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Summarize BEVFormer JSON or JSONL logs"
    )
    parser.add_argument(
        "logs",
        nargs="+",
        type=Path,
        help="one or more log paths",
    )
    parser.add_argument(
        "--metric",
        required=True,
        help="metric key to summarize, e.g. NDS or bbox_mAP",
    )
    return parser.parse_args()


def coerce_numbers(value):
    if isinstance(value, bool):
        return []
    if isinstance(value, (int, float)):
        return [float(value)]
    if isinstance(value, str):
        try:
            return [float(value)]
        except ValueError:
            return []
    if isinstance(value, (list, tuple)):
        numbers = []
        for item in value:
            numbers.extend(coerce_numbers(item))
        return numbers
    return []


def iter_parsed_records(parsed):
    if isinstance(parsed, dict):
        yield parsed
    elif isinstance(parsed, list):
        for item in parsed:
            if isinstance(item, dict):
                yield item


def iter_records(path):
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        print(f"{path}: {exc}", file=sys.stderr)
        return None

    stripped = text.lstrip()
    if not stripped:
        return []

    if stripped[0] in "[{":
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            pass
        else:
            return list(iter_parsed_records(parsed))

    records = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        records.extend(iter_parsed_records(parsed))
    return records


def metric_values(record, metric):
    metric_low = metric.lower()
    fallback = []

    for key, value in record.items():
        if not isinstance(key, str):
            continue
        key_low = key.lower()
        numbers = coerce_numbers(value)
        if not numbers:
            continue
        if key_low == metric_low:
            return numbers
        if key_low.endswith(metric_low):
            prefix = key_low[:-len(metric_low)]
            if not prefix or prefix[-1] in SEPARATORS:
                if not fallback:
                    fallback = numbers

    return fallback


def collect_series(records, metric):
    series = []
    for record in records:
        series.extend(metric_values(record, metric))
    return series


def pick_axis(records):
    for axis_name in PREFERRED_AXIS_KEYS:
        values = collect_series(records, axis_name)
        if values:
            return axis_name, values
    return None, []


def unique_metrics(metric):
    ordered = []
    seen = set()
    for name in (metric, "loss", "lr"):
        lowered = name.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        ordered.append(name)
    return ordered


def fmt(value):
    if isinstance(value, float):
        if not math.isfinite(value):
            return str(value)
        if value.is_integer():
            return str(int(value))
    return f"{value:.6g}" if isinstance(value, float) else str(value)


def summarize_series(series):
    if not series:
        return "not found"

    total = sum(series)
    return (
        f"n={len(series)} first={fmt(series[0])} last={fmt(series[-1])} "
        f"min={fmt(min(series))} max={fmt(max(series))} mean={fmt(total / len(series))}"
    )


def print_summary(path, metric):
    records = iter_records(path)
    if records is None:
        return None

    print(path)

    if not records:
        print("  records=0")
        print("  no JSON records found")
        return False

    print(f"  records={len(records)}")

    axis_name, axis_values = pick_axis(records)
    if axis_values:
        print(f"  axis={axis_name} {fmt(axis_values[0])}..{fmt(axis_values[-1])}")

    for name in unique_metrics(metric):
        series = collect_series(records, name)
        print(f"  {name}: {summarize_series(series)}")

    return True


def main():
    args = parse_args()
    had_success = False
    had_error = False

    for index, path in enumerate(args.logs):
        if index:
            print()
        result = print_summary(path, args.metric)
        if result is True:
            had_success = True
        elif result is None:
            had_error = True

    if had_success and not had_error:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
