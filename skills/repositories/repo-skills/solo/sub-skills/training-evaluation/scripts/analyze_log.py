#!/usr/bin/env python3
"""Bounded JSON-lines analyzer for legacy MMDetection training logs.

This helper deliberately uses only the Python standard library. It reads local
JSON-lines logs, summarizes epochs/metrics/timing, and optionally writes a CSV
for one metric. It never imports MMDetection, executes config code, plots, or
modifies the input log.
"""
from __future__ import print_function

import argparse
import csv
import json
import math
import os
import sys
from collections import defaultdict

DEFAULT_MAX_BYTES = 50 * 1024 * 1024
DEFAULT_MAX_RECORDS = 200000
DEFAULT_MAX_LINE_BYTES = 1024 * 1024


def _finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _numbers(value):
    if _finite_number(value):
        return [float(value)]
    if isinstance(value, (list, tuple)):
        return [float(item) for item in value if _finite_number(item)]
    return []


def _epoch_number(value):
    if isinstance(value, bool):
        raise ValueError("epoch must be numeric")
    try:
        epoch = float(value)
    except (TypeError, ValueError):
        raise ValueError("epoch must be numeric")
    if not math.isfinite(epoch):
        raise ValueError("epoch must be finite")
    return int(epoch) if epoch.is_integer() else epoch


def load_records(path, max_bytes, max_records, max_line_bytes):
    size = os.path.getsize(path)
    if size > max_bytes:
        raise ValueError("log is {} bytes; limit is {} bytes".format(size, max_bytes))

    records = []
    with open(path, "r", encoding="utf-8") as stream:
        for line_no, raw in enumerate(stream, 1):
            if len(raw.encode("utf-8")) > max_line_bytes:
                raise ValueError("line {} exceeds {} bytes".format(line_no, max_line_bytes))
            text = raw.strip()
            if not text:
                continue
            if len(records) >= max_records:
                raise ValueError("record limit {} exceeded".format(max_records))
            try:
                item = json.loads(text)
            except ValueError as exc:
                raise ValueError("invalid JSON at line {}: {}".format(line_no, exc))
            if not isinstance(item, dict):
                raise ValueError("line {} is not a JSON object".format(line_no))
            if "epoch" not in item:
                raise ValueError("line {} has no epoch field".format(line_no))
            item = dict(item)
            item["epoch"] = _epoch_number(item["epoch"])
            item["_line"] = line_no
            records.append(item)
    if not records:
        raise ValueError("log contains no JSON records")
    return records


def metric_names(records):
    names = set()
    for record in records:
        for key, value in record.items():
            if key.startswith("_") or key in ("epoch", "iter", "mode"):
                continue
            if _numbers(value):
                names.add(key)
    return sorted(names)


def mean(values):
    return sum(values) / len(values) if values else None


def describe(records, include_outliers=False):
    epochs = sorted({record["epoch"] for record in records})
    by_epoch = defaultdict(list)
    for record in records:
        by_epoch[record["epoch"]].append(record)

    times_by_epoch = {}
    for epoch, epoch_records in by_epoch.items():
        values = []
        for record in epoch_records:
            values.extend(_numbers(record.get("time")))
        if not include_outliers and len(values) > 1:
            values = values[1:]
        if values:
            times_by_epoch[epoch] = mean(values)

    print("records: {}".format(len(records)))
    print("epochs: {}".format(", ".join(str(epoch) for epoch in epochs)))
    print("metrics: {}".format(", ".join(metric_names(records)) or "none"))
    if times_by_epoch:
        ordered = sorted(times_by_epoch.items(), key=lambda pair: pair[0])
        fastest = min(ordered, key=lambda pair: pair[1])
        slowest = max(ordered, key=lambda pair: pair[1])
        values = [value for _, value in ordered]
        avg = mean(values)
        variance = mean([(value - avg) ** 2 for value in values])
        print("fastest_epoch: {} ({:.6f} s/iter)".format(fastest[0], fastest[1]))
        print("slowest_epoch: {} ({:.6f} s/iter)".format(slowest[0], slowest[1]))
        print("average_iter_time: {:.6f} s/iter".format(avg))
        print("time_std_over_epochs: {:.6f}".format(math.sqrt(variance)))
    else:
        print("timing: no finite time values")


def metric_rows(records, metric):
    rows = []
    for record in records:
        values = _numbers(record.get(metric))
        for index, value in enumerate(values):
            rows.append({
                "epoch": record["epoch"],
                "iter": record.get("iter", ""),
                "mode": record.get("mode", ""),
                "value_index": index,
                "value": value,
                "source_line": record["_line"],
            })
    return rows


def write_metric_csv(path, rows):
    parent = os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(parent):
        raise ValueError("output directory does not exist: {}".format(parent))
    with open(path, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["epoch", "iter", "mode", "value_index", "value", "source_line"],
        )
        writer.writeheader()
        writer.writerows(rows)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Bounded JSON-lines log analyzer")
    parser.add_argument("log", help="local JSON-lines log file")
    parser.add_argument("--summary", action="store_true", help="print record, metric, and timing summary")
    parser.add_argument("--metric", help="numeric metric key to export as rows")
    parser.add_argument("--time", action="store_true", help="include timing summary")
    parser.add_argument("--include-outliers", action="store_true", help="include first timing value of each epoch")
    parser.add_argument("--out", help="CSV output path for --metric")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--max-records", type=int, default=DEFAULT_MAX_RECORDS)
    parser.add_argument("--max-line-bytes", type=int, default=DEFAULT_MAX_LINE_BYTES)
    args = parser.parse_args(argv)
    if not (args.summary or args.metric or args.time):
        parser.error("choose at least one of --summary, --time, or --metric")
    if args.out and not args.metric:
        parser.error("--out requires --metric")
    for name in ("max_bytes", "max_records", "max_line_bytes"):
        if getattr(args, name) <= 0:
            parser.error("--{} must be positive".format(name.replace("_", "-")))
    return args


def main(argv=None):
    args = parse_args(argv)
    try:
        records = load_records(args.log, args.max_bytes, args.max_records, args.max_line_bytes)
        if args.summary or args.time:
            describe(records, include_outliers=args.include_outliers)
        if args.metric:
            rows = metric_rows(records, args.metric)
            if not rows:
                raise ValueError("metric {!r} has no finite numeric values".format(args.metric))
            if args.out:
                write_metric_csv(args.out, rows)
                print("wrote {} rows to {}".format(len(rows), args.out))
            else:
                writer = csv.DictWriter(
                    sys.stdout,
                    fieldnames=["epoch", "iter", "mode", "value_index", "value", "source_line"],
                )
                writer.writeheader()
                writer.writerows(rows)
    except (OSError, ValueError) as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
