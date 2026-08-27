#!/usr/bin/env python3
"""Summarize Boltz confidence/affinity JSON files and benchmark CSV columns.

This helper intentionally avoids importing Boltz, OpenStructure, pandas, or any
source-repository modules. It is for local output inspection and CSV aggregation,
not for reproducing structural benchmark metrics from target structures.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

IDENTIFIER_COLUMNS = {
    "id",
    "name",
    "target",
    "tool",
    "model",
    "model_id",
    "model_idx",
    "record_type",
    "source",
    "dataset",
    "split",
}

MODEL_RE = re.compile(r"_model_(\d+)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize Boltz confidence/affinity JSON outputs and numeric CSV "
            "metrics without requiring benchmark targets or OpenStructure."
        )
    )
    parser.add_argument(
        "--predictions-dir",
        action="append",
        type=Path,
        default=[],
        help=(
            "Prediction directory to scan recursively for confidence_*.json and "
            "affinity_*.json files. May be passed more than once."
        ),
    )
    parser.add_argument(
        "--csv",
        action="append",
        type=Path,
        default=[],
        help=(
            "CSV file to summarize. Long-form metric,value files and wide-form "
            "numeric metric columns are both supported. May be passed more than once."
        ),
    )
    parser.add_argument(
        "--metric",
        action="append",
        default=[],
        help="Metric/column name to include. By default all numeric metrics are included.",
    )
    parser.add_argument(
        "--include-nested",
        action="store_true",
        help="Include nested numeric JSON fields as dotted metric names.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Write summary CSV to this path instead of stdout.",
    )
    parser.add_argument(
        "--records-out",
        type=Path,
        help="Optionally write flattened per-record metric values to this CSV path.",
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Exit non-zero if non-fatal input warnings were encountered.",
    )
    args = parser.parse_args()
    if not args.predictions_dir and not args.csv:
        parser.error("provide at least one --predictions-dir or --csv")
    return args


def warn(warnings: list[str], message: str) -> None:
    warnings.append(message)
    print(f"warning: {message}", file=sys.stderr)


def as_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None
    return None


def flatten_numeric_json(
    data: dict[str, Any], *, include_nested: bool, prefix: str = ""
) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for key, value in data.items():
        metric = f"{prefix}.{key}" if prefix else key
        number = as_float(value)
        if number is not None:
            metrics[metric] = number
        elif include_nested and isinstance(value, dict):
            metrics.update(
                flatten_numeric_json(value, include_nested=include_nested, prefix=metric)
            )
    return metrics


def metric_direction_and_note(record_type: str, metric: str) -> tuple[str, str]:
    metric_lower = metric.lower()
    if "affinity_probability_binary" in metric_lower:
        return "higher", "binder probability; keep separate from affinity value"
    if "affinity_pred_value" in metric_lower:
        return "lower", "log10(IC50 in micromolar); compare active binders"
    if "rmsd" in metric_lower:
        return "lower", "distance error metric"
    if metric_lower.endswith("pde") or "_pde" in metric_lower or ".pde" in metric_lower:
        return "lower", "predicted distance error in angstroms"
    if metric_lower in {"lddt", "bb_lddt", "tm_score", "ptm", "iptm"}:
        return "higher", "structural or predicted-structure confidence score"
    if "plddt" in metric_lower or "confidence" in metric_lower or "probability" in metric_lower:
        return "higher", "model confidence or probability score"
    if "dockq" in metric_lower or "valid" in metric_lower:
        return "higher", "benchmark quality or validity score"
    if record_type == "affinity_json":
        return "check", "affinity field; verify semantics before ranking"
    return "check", "verify metric direction from the producing workflow"


def prediction_record_type(path: Path) -> str | None:
    name = path.name
    if name.startswith("confidence_") and name.endswith(".json"):
        return "confidence_json"
    if name.startswith("affinity_") and name.endswith(".json"):
        return "affinity_json"
    return None


def target_from_prediction_file(path: Path) -> str:
    return path.parent.name


def model_from_prediction_file(path: Path) -> str:
    match = MODEL_RE.search(path.stem)
    return match.group(1) if match else ""


def scan_prediction_dir(
    root: Path,
    requested_metrics: set[str],
    include_nested: bool,
    warnings: list[str],
) -> list[dict[str, str | float]]:
    if not root.exists():
        warn(warnings, f"prediction directory does not exist: {root}")
        return []
    if not root.is_dir():
        warn(warnings, f"prediction path is not a directory: {root}")
        return []

    files = sorted(
        path for path in root.rglob("*.json") if prediction_record_type(path) is not None
    )
    if not files:
        warn(warnings, f"no confidence_*.json or affinity_*.json files under: {root}")
        return []

    records: list[dict[str, str | float]] = []
    for path in files:
        record_type = prediction_record_type(path)
        if record_type is None:
            continue
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            warn(warnings, f"could not read JSON {path}: {exc}")
            continue
        if not isinstance(data, dict):
            warn(warnings, f"JSON root is not an object: {path}")
            continue

        metrics = flatten_numeric_json(data, include_nested=include_nested)
        if requested_metrics:
            metrics = {k: v for k, v in metrics.items() if k in requested_metrics}
        if not metrics:
            warn(warnings, f"no requested numeric metrics found in: {path}")
            continue

        for metric, value in metrics.items():
            records.append(
                {
                    "source": str(path),
                    "source_kind": "prediction_json",
                    "record_type": record_type,
                    "target": target_from_prediction_file(path),
                    "tool": "boltz",
                    "model": model_from_prediction_file(path),
                    "metric": metric,
                    "value": value,
                }
            )
    return records


def read_csv_rows(path: Path, warnings: list[str]) -> tuple[list[dict[str, str]], list[str]]:
    if not path.exists():
        warn(warnings, f"CSV file does not exist: {path}")
        return [], []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames or []
            rows = list(reader)
    except OSError as exc:
        warn(warnings, f"could not read CSV {path}: {exc}")
        return [], []
    if not fieldnames:
        warn(warnings, f"CSV has no header: {path}")
    elif not rows:
        warn(warnings, f"CSV has no data rows: {path}")
    return rows, fieldnames


def scan_csv_file(
    path: Path, requested_metrics: set[str], warnings: list[str]
) -> list[dict[str, str | float]]:
    rows, fieldnames = read_csv_rows(path, warnings)
    if not rows or not fieldnames:
        return []

    records: list[dict[str, str | float]] = []
    lower_fields = {name.lower(): name for name in fieldnames}
    metric_field = lower_fields.get("metric")
    value_field = lower_fields.get("value")

    if metric_field and value_field:
        for row_index, row in enumerate(rows, start=2):
            metric = (row.get(metric_field) or "").strip()
            if not metric or (requested_metrics and metric not in requested_metrics):
                continue
            value = as_float(row.get(value_field))
            if value is None:
                warn(warnings, f"non-numeric value in {path} row {row_index} metric {metric}")
                continue
            records.append(
                {
                    "source": str(path),
                    "source_kind": "csv",
                    "record_type": "csv_long",
                    "target": row.get(lower_fields.get("target", ""), ""),
                    "tool": row.get(lower_fields.get("tool", ""), ""),
                    "model": row.get(lower_fields.get("model", ""), ""),
                    "metric": metric,
                    "value": value,
                }
            )
        if not records:
            warn(warnings, f"no numeric long-form metric rows found in: {path}")
        return records

    numeric_columns: list[str] = []
    for field in fieldnames:
        field_key = field.strip().lower()
        if field_key in IDENTIFIER_COLUMNS:
            continue
        if requested_metrics and field not in requested_metrics:
            continue
        if any(as_float(row.get(field)) is not None for row in rows):
            numeric_columns.append(field)

    if not numeric_columns:
        warn(warnings, f"no numeric metric columns found in CSV: {path}")
        return []

    for row_index, row in enumerate(rows, start=2):
        for metric in numeric_columns:
            value = as_float(row.get(metric))
            if value is None:
                continue
            records.append(
                {
                    "source": str(path),
                    "source_kind": "csv",
                    "record_type": "csv_wide",
                    "target": row.get(lower_fields.get("target", ""), ""),
                    "tool": row.get(lower_fields.get("tool", ""), ""),
                    "model": row.get(lower_fields.get("model", ""), ""),
                    "metric": metric,
                    "value": value,
                }
            )
    return records


def format_number(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.10g}"


def summarize(records: Iterable[dict[str, str | float]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, str | float]]] = defaultdict(list)
    for record in records:
        key = (
            str(record.get("source_kind", "")),
            str(record.get("record_type", "")),
            str(record.get("tool", "")),
            str(record.get("metric", "")),
        )
        grouped[key].append(record)

    rows: list[dict[str, str]] = []
    for (source_kind, record_type, tool, metric), group in sorted(grouped.items()):
        values = [float(record["value"]) for record in group]
        targets = {str(record.get("target", "")) for record in group if record.get("target")}
        models = {str(record.get("model", "")) for record in group if record.get("model")}
        direction, note = metric_direction_and_note(record_type, metric)
        rows.append(
            {
                "source_kind": source_kind,
                "record_type": record_type,
                "tool": tool,
                "metric": metric,
                "count": str(len(values)),
                "target_count": str(len(targets)),
                "model_count": str(len(models)),
                "mean": format_number(statistics.fmean(values)),
                "median": format_number(statistics.median(values)),
                "min": format_number(min(values)),
                "max": format_number(max(values)),
                "stdev": format_number(statistics.stdev(values) if len(values) > 1 else None),
                "direction": direction,
                "note": note,
            }
        )
    return rows


def write_csv(path: Path | None, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    if path is None:
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_records(path: Path, records: list[dict[str, str | float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source",
        "source_kind",
        "record_type",
        "target",
        "tool",
        "model",
        "metric",
        "value",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def main() -> int:
    args = parse_args()
    requested_metrics = set(args.metric)
    warnings: list[str] = []

    records: list[dict[str, str | float]] = []
    for root in args.predictions_dir:
        records.extend(
            scan_prediction_dir(root, requested_metrics, args.include_nested, warnings)
        )
    for csv_path in args.csv:
        records.extend(scan_csv_file(csv_path, requested_metrics, warnings))

    if args.records_out:
        write_records(args.records_out, records)

    if not records:
        warn(warnings, "no metric records were collected")
        return 2

    summary_rows = summarize(records)
    summary_fields = [
        "source_kind",
        "record_type",
        "tool",
        "metric",
        "count",
        "target_count",
        "model_count",
        "mean",
        "median",
        "min",
        "max",
        "stdev",
        "direction",
        "note",
    ]
    write_csv(args.out, summary_rows, summary_fields)

    if warnings and args.fail_on_warning:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
