#!/usr/bin/env python3
"""Summarize Diffusion Policy train_*/logs.json.txt files offline.

No W&B, Ray, simulator, dataset, or network calls are made.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

Number = float | int


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def train_dir_key(path: Path) -> Tuple[int, int | str]:
    match = re.fullmatch(r"train_(\d+)", path.name)
    if match:
        return (0, int(match.group(1)))
    return (1, path.name)


def load_json_lines(path: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    records: List[Dict[str, Any]] = []
    warnings: List[str] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                warnings.append(f"ignored incomplete/invalid JSON line {line_no} in {path}")
                break
            if isinstance(record, dict):
                records.append(record)
            else:
                warnings.append(f"ignored non-object JSON line {line_no} in {path}")
    return records, warnings


def summarize_key(records: List[Dict[str, Any]], key: str) -> Dict[str, Any] | None:
    series: List[Tuple[int, Dict[str, Any], float]] = []
    for idx, record in enumerate(records):
        if key not in record:
            continue
        value = record[key]
        if not is_number(value):
            continue
        series.append((idx, record, float(value)))
    if not series:
        return None

    values = [v for _, _, v in series]
    max_idx, max_record, max_value = max(series, key=lambda item: item[2])
    min_idx, min_record, min_value = min(series, key=lambda item: item[2])
    last_idx, last_record, last_value = series[-1]

    result: Dict[str, Any] = {
        "count": len(values),
        "first": values[0],
        "last": last_value,
        "min": min_value,
        "max": max_value,
        "mean": statistics.fmean(values),
        "std": statistics.pstdev(values) if len(values) > 1 else 0.0,
        "best_index": max_idx,
        "best_global_step": max_record.get("global_step"),
        "best_epoch": max_record.get("epoch"),
        "last_global_step": last_record.get("global_step"),
        "last_epoch": last_record.get("epoch"),
        "min_index": min_idx,
        "min_global_step": min_record.get("global_step"),
        "min_epoch": min_record.get("epoch"),
    }
    return result


def aggregate_key(per_run: Dict[str, Dict[str, Any]], key: str) -> Dict[str, Any]:
    summaries = [run_data[key] for run_data in per_run.values() if key in run_data]
    result: Dict[str, Any] = {"runs": len(summaries)}
    for metric in ("last", "max", "min", "mean"):
        values = [float(summary[metric]) for summary in summaries if metric in summary and is_number(summary[metric])]
        if not values:
            continue
        result[f"{metric}_mean"] = statistics.fmean(values)
        result[f"{metric}_std"] = statistics.pstdev(values) if len(values) > 1 else 0.0
    return result


def summarize_run_dir(run_dir: Path, keys: Sequence[str]) -> Dict[str, Any]:
    warnings: List[str] = []
    train_dirs = sorted([p for p in run_dir.glob("train_*") if p.is_dir()], key=train_dir_key)
    if not train_dirs:
        raise FileNotFoundError(f"no train_* directories found under {run_dir}")

    runs: Dict[str, Dict[str, Any]] = {}
    log_files: Dict[str, str] = {}
    for train_dir in train_dirs:
        log_path = train_dir / "logs.json.txt"
        if not log_path.is_file():
            warnings.append(f"missing log file: {log_path}")
            continue
        records, load_warnings = load_json_lines(log_path)
        warnings.extend(load_warnings)
        run_summary: Dict[str, Any] = {}
        for key in keys:
            summary = summarize_key(records, key)
            if summary is None:
                warnings.append(f"key {key!r} not found as numeric value in {log_path}")
            else:
                run_summary[key] = summary
        runs[train_dir.name] = run_summary
        log_files[train_dir.name] = str(log_path)

    aggregate = {key: aggregate_key(runs, key) for key in keys}
    return {
        "run_dir": str(run_dir),
        "keys": list(keys),
        "log_files": log_files,
        "runs": runs,
        "aggregate": aggregate,
        "warnings": warnings,
    }


def fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def print_table(summary: Dict[str, Any]) -> None:
    print(f"run_dir: {summary['run_dir']}")
    warnings = summary.get("warnings", [])
    for key in summary["keys"]:
        print(f"\nkey: {key}")
        rows: List[List[str]] = []
        for run_name, run_data in summary["runs"].items():
            item = run_data.get(key)
            if not item:
                rows.append([run_name, "missing", "-", "-", "-", "-", "-", "-"])
                continue
            rows.append([
                run_name,
                fmt(item.get("count")),
                fmt(item.get("last")),
                fmt(item.get("max")),
                fmt(item.get("mean")),
                fmt(item.get("std")),
                fmt(item.get("best_epoch")),
                fmt(item.get("best_global_step")),
            ])
        header = ["run", "count", "last", "max", "mean", "std", "best_epoch", "best_step"]
        widths = [max(len(row[i]) for row in ([header] + rows)) for i in range(len(header))]
        print("  " + "  ".join(header[i].ljust(widths[i]) for i in range(len(header))))
        print("  " + "  ".join("-" * widths[i] for i in range(len(header))))
        for row in rows:
            print("  " + "  ".join(row[i].ljust(widths[i]) for i in range(len(header))))
        agg = summary["aggregate"].get(key, {})
        print(
            "  aggregate: "
            f"runs={fmt(agg.get('runs'))}, "
            f"last_mean={fmt(agg.get('last_mean'))}, last_std={fmt(agg.get('last_std'))}, "
            f"max_mean={fmt(agg.get('max_mean'))}, max_std={fmt(agg.get('max_std'))}"
        )
    if warnings:
        print("\nwarnings:", file=sys.stderr)
        for warning in warnings:
            print(f"  - {warning}", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize Diffusion Policy train_*/logs.json.txt files without W&B or Ray.",
    )
    parser.add_argument(
        "--run-dir",
        required=True,
        help="Multirun root directory containing train_*/logs.json.txt.",
    )
    parser.add_argument(
        "--key",
        action="append",
        default=None,
        metavar="METRIC",
        help="Metric key to summarize. Repeat for multiple keys. Default: test/mean_score.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a table.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_dir = Path(args.run_dir).expanduser().resolve()
    keys = args.key or ["test/mean_score"]
    if not run_dir.is_dir():
        print(f"error: run directory not found: {run_dir}", file=sys.stderr)
        return 2
    try:
        summary = summarize_run_dir(run_dir, keys)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_table(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
