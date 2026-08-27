#!/usr/bin/env python3
"""Summarize VLMEvalKit status.json run directories without importing vlmeval."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from numbers import Real
from pathlib import Path
from typing import Any

FAIL_MSG = "Failed to obtain answer"
PRED_SUFFIXES = (".xlsx", ".tsv", ".json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--work-dir",
        type=Path,
        action="append",
        required=True,
        help="A run directory containing status.json, or a model root whose latest child run contains status.json.",
    )
    parser.add_argument("--data", nargs="+", default=None, help="Optional dataset filter/order.")
    parser.add_argument("--verbose", action="store_true", help="Print detailed per-dataset rows. Supports one --work-dir.")
    parser.add_argument("--fail-substring", default=FAIL_MSG, help="Substring used to count failed prediction rows.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of CSV/table text.")
    args = parser.parse_args()
    if args.verbose and len(args.work_dir) != 1:
        parser.error("--verbose supports exactly one --work-dir")
    if args.data is not None:
        args.data = list(dict.fromkeys(args.data))
    return args


def resolve_run_dir(path: Path) -> Path:
    path = path.expanduser().resolve()
    if (path / "status.json").exists():
        return path
    candidates = [p for p in path.iterdir() if p.is_dir() and (p / "status.json").exists()] if path.is_dir() else []
    if not candidates:
        raise FileNotFoundError(f"No status.json found in {path} or its direct child directories")
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def load_status(run_dir: Path) -> dict[str, Any]:
    with (run_dir / "status.json").open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"status.json is not an object: {run_dir / 'status.json'}")
    return data


def require_pandas(reason: str):
    try:
        import pandas as pd  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(f"Reading {reason} requires pandas with the appropriate Excel engine installed") from exc
    return pd


def rows_from_json(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [x if isinstance(x, dict) else {"value": x} for x in data]
    if isinstance(data, dict):
        if "columns" in data and "data" in data and isinstance(data["columns"], list):
            return [dict(zip(data["columns"], row)) for row in data.get("data", [])]
        values = list(data.values())
        if values and all(isinstance(v, list) for v in values):
            length = min(len(v) for v in values)
            return [{k: data[k][i] for k in data} for i in range(length)]
        return [data]
    return [{"value": data}]


def load_rows(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return rows_from_json(path)
    if suffix in {".csv", ".tsv"}:
        dialect = "excel-tab" if suffix == ".tsv" else "excel"
        with path.open(newline="", encoding="utf-8") as fh:
            return [dict(row) for row in csv.DictReader(fh, dialect=dialect)]
    if suffix == ".xlsx":
        pd = require_pandas(".xlsx files")
        frame = pd.read_excel(path)
        return frame.to_dict("records")
    raise ValueError(f"Unsupported prediction file type: {path}")


def find_prediction_file(run_dir: Path, model_name: str, dataset_name: str, recorded: str | None) -> Path | None:
    if recorded:
        path = Path(recorded)
        if not path.is_absolute():
            path = run_dir / path
        if path.exists():
            return path
    for suffix in PRED_SUFFIXES:
        path = run_dir / f"{model_name}_{dataset_name}{suffix}"
        if path.exists():
            return path
    return None


def count_prediction_failures(path: Path | None, fail_substring: str) -> tuple[int | None, int | None, str | None]:
    if path is None:
        return None, None, None
    try:
        rows = load_rows(path)
    except Exception as exc:
        return None, None, f"could not read prediction file: {exc}"
    failed = 0
    total = 0
    for row in rows:
        if "prediction" not in row:
            continue
        total += 1
        if fail_substring in str(row.get("prediction")):
            failed += 1
    return failed, total, None


def is_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, Real):
        try:
            return not math.isnan(float(value))
        except Exception:
            return True
    if isinstance(value, str):
        try:
            float(value)
            return True
        except Exception:
            return False
    return False


def format_sigfig(value: Any) -> str:
    if value is None or isinstance(value, bool):
        return "-"
    if is_number(value):
        return f"{float(value):.4g}"
    return str(value)


def format_jsonish(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, (list, tuple, dict)):
        return json.dumps(value, ensure_ascii=False)
    return format_sigfig(value)


def format_fail_rate(failed: int | None, total: int | None) -> str:
    if failed is None or total is None or total <= 0:
        return "-"
    return f"{failed / total * 100:.2f}% ({failed}/{total})"


def truncate(value: Any, limit: int = 120) -> str:
    text = "-" if value in (None, "") else str(value)
    return text if len(text) <= limit else text[:limit] + "..."


def metric_pairs(dataset_status: dict[str, Any]) -> list[tuple[str, Any]]:
    metrics = dataset_status.get("metrics") or {}
    primary = dataset_status.get("primary_metric")
    if isinstance(primary, list):
        if not primary:
            return [("-", None)]
        return [(str(metric), metrics.get(metric) if isinstance(metrics, dict) else None) for metric in primary]
    if primary:
        return [(str(primary), metrics.get(primary) if isinstance(metrics, dict) else None)]
    if isinstance(metrics, dict) and len(metrics) == 1:
        key = next(iter(metrics))
        return [(str(key), metrics[key])]
    return [("-", None)]


def collect_verbose_rows(run_dir: Path, status: dict[str, Any], fail_substring: str, dataset_filter: list[str] | None) -> list[dict[str, str]]:
    model_name = str(status.get("model_name") or run_dir.parent.name)
    datasets = status.get("datasets") or {}
    if not isinstance(datasets, dict):
        return []
    names = dataset_filter if dataset_filter is not None else sorted(datasets)
    rows: list[dict[str, str]] = []
    for dataset_name in names:
        ds = datasets.get(dataset_name)
        if not isinstance(ds, dict):
            continue
        pred_file = find_prediction_file(run_dir, model_name, dataset_name, ds.get("prediction_file"))
        failed, total, pred_error = count_prediction_failures(pred_file, fail_substring)
        for idx, (metric, value) in enumerate(metric_pairs(ds)):
            rows.append({
                "model": model_name if idx == 0 else "",
                "run": run_dir.name if idx == 0 else "",
                "benchmark": dataset_name if idx == 0 else "",
                "status": str(ds.get("status") or "-") if idx == 0 else "",
                "infer_fail_rate": format_fail_rate(failed, total) if idx == 0 else "",
                "primary_metric": format_jsonish(metric),
                "primary_metric_value": format_jsonish(value),
                "judge_model": str(ds.get("judge_model") or "-") if idx == 0 else "",
                "source_run": str(ds.get("source_run") or "-") if idx == 0 else "",
                "skip_reason": str(ds.get("skip_reason") or "-") if idx == 0 else "",
                "eval_error": truncate(ds.get("error_message")) if idx == 0 else "",
                "prediction_note": truncate(pred_error) if idx == 0 and pred_error else ("" if idx else "-"),
            })
    return rows


def dedupe(names: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    out: list[str] = []
    for name in names:
        counts[name] = counts.get(name, 0) + 1
        out.append(name if counts[name] == 1 else f"{name}#{counts[name]}")
    return out


def collect_summary(run_reports: list[dict[str, Any]], dataset_filter: list[str] | None) -> tuple[list[dict[str, str]], list[str]]:
    model_columns = dedupe([str(report["model_name"]) for report in run_reports])
    merged: dict[tuple[str, str], dict[str, str]] = {}
    filter_set = set(dataset_filter) if dataset_filter is not None else None

    for model_column, report in zip(model_columns, run_reports):
        datasets = report["status"].get("datasets") or {}
        if not isinstance(datasets, dict):
            continue
        names = dataset_filter if dataset_filter is not None else sorted(datasets)
        for dataset_name in names:
            ds = datasets.get(dataset_name)
            if not isinstance(ds, dict):
                continue
            if filter_set is not None and dataset_name not in filter_set:
                continue
            pairs = metric_pairs(ds)
            if not pairs or pairs == [("-", None)]:
                pairs = [(str(ds.get("status") or "status"), ds.get("skip_reason") or ds.get("error_message") or "-")]
            for metric, value in pairs:
                key = (dataset_name, format_jsonish(metric))
                merged.setdefault(key, {"benchmark": dataset_name, "primary_metric": format_jsonish(metric)})
                merged[key][model_column] = format_jsonish(value)

    ordered_columns = ["benchmark", "primary_metric", *model_columns]
    ordered_keys = sorted(merged) if dataset_filter is None else [key for name in dataset_filter for key in merged if key[0] == name]
    rows = [{column: merged[key].get(column, "-") for column in ordered_columns} for key in ordered_keys]
    return rows, ordered_columns


def print_csv_and_table(rows: list[dict[str, str]], columns: list[str] | None = None) -> None:
    if not rows:
        return
    if columns is None:
        columns = list(rows[0])
    writer = csv.DictWriter(sys.stdout, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: row.get(column, "-") for column in columns})
    print()
    try:
        from tabulate import tabulate  # type: ignore
        print(tabulate([[row.get(c, "-") for c in columns] for row in rows], headers=columns, tablefmt="github"))
    except Exception:
        widths = {c: max(len(c), *(len(str(row.get(c, "-"))) for row in rows)) for c in columns}
        print(" | ".join(c.ljust(widths[c]) for c in columns))
        print("-+-".join("-" * widths[c] for c in columns))
        for row in rows:
            print(" | ".join(str(row.get(c, "-")).ljust(widths[c]) for c in columns))


def main() -> int:
    args = parse_args()
    run_reports = []
    for work_dir in args.work_dir:
        run_dir = resolve_run_dir(work_dir)
        status = load_status(run_dir)
        run_reports.append({
            "run_dir": str(run_dir),
            "model_name": str(status.get("model_name") or run_dir.parent.name),
            "status": status,
        })

    if args.verbose:
        run_dir = Path(run_reports[0]["run_dir"])
        rows = collect_verbose_rows(run_dir, run_reports[0]["status"], args.fail_substring, args.data)
        if args.json:
            print(json.dumps(rows, indent=2, ensure_ascii=False))
        else:
            print_csv_and_table(rows)
        return 0

    rows, columns = collect_summary(run_reports, args.data)
    if args.json:
        print(json.dumps({"columns": columns, "rows": rows}, indent=2, ensure_ascii=False))
    else:
        print_csv_and_table(rows, columns)
    return 0


if __name__ == "__main__":
    sys.exit(main())
