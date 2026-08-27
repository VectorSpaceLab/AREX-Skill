#!/usr/bin/env python3
"""Summarize AiZynthFinder JSON, JSON.GZ, HDF5, or checkpoint outputs."""

from __future__ import annotations

import argparse
import gzip
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

EXPECTED_COLUMNS = [
    "target",
    "search_time",
    "first_solution_time",
    "first_solution_iteration",
    "number_of_nodes",
    "max_transforms",
    "max_children",
    "number_of_routes",
    "number_of_solved_routes",
    "top_score",
    "is_solved",
    "number_of_steps",
    "number_of_precursors",
    "number_of_precursors_in_stock",
    "precursors_in_stock",
    "precursors_not_in_stock",
    "precursors_availability",
    "policy_used_counts",
    "profiling",
    "stock_info",
    "top_scores",
    "trees",
]

HDF_SUFFIXES = {".h5", ".hdf", ".hdf5"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print a safe summary of an AiZynthFinder output table or checkpoint. "
            "Tree summaries are written only when --write-tree-summary is supplied."
        )
    )
    parser.add_argument("output", type=Path, help="AiZynthFinder output file to summarize")
    parser.add_argument(
        "--format",
        choices=("auto", "json-table", "hdf", "checkpoint"),
        default="auto",
        help="Input format override; default infers from extension and content",
    )
    parser.add_argument(
        "--hdf-key",
        default="table",
        help="HDF5 key for table output; AiZynthFinder uses 'table' by default",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=5,
        help="Number of target identifiers to show",
    )
    parser.add_argument(
        "--write-tree-summary",
        type=Path,
        help=(
            "Optional JSON path for compact tree availability summaries. "
            "No tree data is written unless this option is provided."
        ),
    )
    return parser.parse_args()


def fail(message: str, exit_code: int = 1) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def infer_format(path: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    suffixes = [suffix.lower() for suffix in path.suffixes]
    if suffixes and suffixes[-1] in HDF_SUFFIXES:
        return "hdf"
    if len(suffixes) >= 2 and suffixes[-2] in HDF_SUFFIXES and suffixes[-1] == ".gz":
        return "hdf"
    if "checkpoint" in path.name.lower():
        return "checkpoint"
    return "json-table"


def open_text(path: Path):
    if path.suffix.lower() == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("rt", encoding="utf-8")


def read_hdf_rows(path: Path, hdf_key: str) -> tuple[list[dict[str, Any]], list[str]]:
    try:
        import pandas as pd  # type: ignore
    except ImportError as err:
        fail(
            "pandas with HDF5/PyTables support is required to read HDF5 outputs; "
            f"pandas import failed with: {err}"
        )
    try:
        data = pd.read_hdf(path, hdf_key)
    except Exception as err:  # noqa: BLE001 - report optional dependency/key issues
        fail(f"failed to read HDF5 table with key {hdf_key!r}: {err}")
    rows = data.to_dict(orient="records")
    return rows, [str(column) for column in data.columns]


def read_json_table_rows(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    try:
        with open_text(path) as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as err:
        records = read_checkpoint_records(path, allow_empty=True)
        if records:
            return records, collect_columns(records)
        fail(
            "failed to read JSON as pandas orient='table' output; "
            f"checkpoint fallback also found no records: {err}"
        )
    except OSError as err:
        fail(f"failed to read JSON output: {err}")

    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        rows = [row for row in payload["data"] if isinstance(row, dict)]
        columns = columns_from_table_schema(payload) or collect_columns(rows)
        columns = [column for column in columns if column != "index"]
        rows = [{key: value for key, value in row.items() if key != "index"} for row in rows]
        return rows, columns

    if isinstance(payload, list):
        if all(isinstance(row, dict) for row in payload):
            rows = list(payload)
            return rows, collect_columns(rows)
        return [{"trees": payload}], ["trees"]

    if isinstance(payload, dict):
        if looks_like_tree_dict(payload):
            return [{"target": payload.get("smiles", "tree-0"), "trees": [payload]}], ["target", "trees"]
        return [payload], collect_columns([payload])

    fail("JSON payload is not a table, object, list, or tree dictionary")


def columns_from_table_schema(payload: dict[str, Any]) -> list[str]:
    schema = payload.get("schema")
    if not isinstance(schema, dict):
        return []
    fields = schema.get("fields")
    if not isinstance(fields, list):
        return []
    columns = []
    for field in fields:
        if isinstance(field, dict) and isinstance(field.get("name"), str):
            columns.append(field["name"])
    return columns


def looks_like_tree_dict(payload: dict[str, Any]) -> bool:
    return payload.get("type") in {"mol", "reaction"} and "smiles" in payload


def read_checkpoint_records(path: Path, allow_empty: bool) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        with open_text(path) as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError as err:
                    if allow_empty:
                        return []
                    fail(f"line {line_number} is not valid JSON: {err}")
                if not isinstance(record, dict):
                    if allow_empty:
                        return []
                    fail(f"line {line_number} is JSON but not an object")
                records.append(record)
    except OSError as err:
        if allow_empty:
            return []
        fail(f"failed to read checkpoint text: {err}")
    if not records and not allow_empty:
        fail("checkpoint contained no JSON records")
    return records


def read_rows(path: Path, input_format: str, hdf_key: str) -> tuple[str, list[dict[str, Any]], list[str]]:
    if input_format == "hdf":
        rows, columns = read_hdf_rows(path, hdf_key)
        return "hdf", rows, columns
    if input_format == "checkpoint":
        rows = read_checkpoint_records(path, allow_empty=False)
        return "checkpoint", rows, collect_columns(rows)
    rows, columns = read_json_table_rows(path)
    return "json-table", rows, columns


def collect_columns(rows: Iterable[dict[str, Any]]) -> list[str]:
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                columns.append(key)
    return columns


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(value is not value or math.isnan(value))
    except TypeError:
        return False


def truthy_count(values: Iterable[Any]) -> int:
    count = 0
    for value in values:
        if is_missing(value):
            continue
        if isinstance(value, str):
            count += value.strip().lower() in {"true", "1", "yes", "y"}
        else:
            count += bool(value)
    return count


def numeric_summary(values: Iterable[Any]) -> dict[str, float] | None:
    numeric: list[float] = []
    for value in values:
        if is_missing(value):
            continue
        try:
            numeric.append(float(value))
        except (TypeError, ValueError):
            continue
    if not numeric:
        return None
    return {
        "min": min(numeric),
        "mean": sum(numeric) / len(numeric),
        "max": max(numeric),
    }


def tree_count(value: Any) -> int | None:
    if is_missing(value):
        return None
    if isinstance(value, list):
        return len(value)
    if isinstance(value, tuple):
        return len(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return 0
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, list):
            return len(parsed)
        if isinstance(parsed, dict):
            return 1
    if isinstance(value, dict):
        return 1
    return None


def get_target(row: dict[str, Any], index: int) -> str:
    for key in ("target", "smiles"):
        if key in row and not is_missing(row[key]):
            return str(row[key])
    return f"row-{index}"


def column_values(rows: list[dict[str, Any]], column: str) -> list[Any]:
    return [row.get(column) for row in rows]


def print_summary(kind: str, rows: list[dict[str, Any]], columns: list[str], sample_size: int) -> None:
    row_count = len(rows)
    print(f"format: {kind}")
    print(f"rows: {row_count}")
    print(f"columns: {', '.join(columns) if columns else '(none)'}")

    missing_columns = [column for column in EXPECTED_COLUMNS if column not in columns]
    if missing_columns:
        print(f"missing_expected_columns: {', '.join(missing_columns)}")
    else:
        print("missing_expected_columns: none")

    if "is_solved" in columns:
        solved = truthy_count(column_values(rows, "is_solved"))
        print(f"solved_count: {solved}")
    elif "number_of_solved_routes" in columns:
        solved_values = numeric_summary(column_values(rows, "number_of_solved_routes"))
        if solved_values is None:
            print("rows_with_solved_routes: unavailable")
        else:
            count = 0
            for value in column_values(rows, "number_of_solved_routes"):
                try:
                    count += float(value) > 0
                except (TypeError, ValueError):
                    pass
            print(f"rows_with_solved_routes: {count}")
    else:
        print("solved_count: unavailable")

    if "top_score" in columns:
        summary = numeric_summary(column_values(rows, "top_score"))
        if summary is None:
            print("top_score: present but not numeric")
        else:
            print(
                "top_score: "
                f"min={summary['min']:.6g}, mean={summary['mean']:.6g}, max={summary['max']:.6g}"
            )
    else:
        print("top_score: unavailable")

    target_column = "target" if "target" in columns else "smiles" if "smiles" in columns else None
    if target_column:
        samples = [str(row.get(target_column)) for row in rows[: max(sample_size, 0)]]
        print(f"sample_targets: {', '.join(samples) if samples else '(none)'}")
    else:
        print("sample_targets: unavailable")

    if "trees" in columns:
        counts = [tree_count(row.get("trees")) for row in rows]
        known_counts = [count for count in counts if count is not None]
        missing_count = sum(1 for count in counts if count is None)
        zero_count = sum(1 for count in known_counts if count == 0)
        total_trees = sum(known_counts)
        print(f"tree_rows: {len(known_counts)} readable, {missing_count} unknown")
        print(f"tree_count_total: {total_trees}")
        print(f"tree_rows_empty: {zero_count}")
    else:
        print("trees: column missing")


def write_tree_summary(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    summary_rows: list[dict[str, Any]] = []
    has_trees = "trees" in columns
    for index, row in enumerate(rows):
        entry = {
            "row": index,
            "target": get_target(row, index),
            "has_trees_column": has_trees,
            "tree_count": tree_count(row.get("trees")) if has_trees else None,
        }
        if "is_solved" in columns and not is_missing(row.get("is_solved")):
            entry["is_solved"] = bool(row.get("is_solved"))
        if "top_score" in columns and not is_missing(row.get("top_score")):
            try:
                entry["top_score"] = float(row.get("top_score"))
            except (TypeError, ValueError):
                entry["top_score"] = str(row.get("top_score"))
        summary_rows.append(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary_rows, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"wrote_tree_summary: {path}")


def main() -> None:
    args = parse_args()
    if not args.output.exists():
        fail(f"input file does not exist: {args.output}")
    input_format = infer_format(args.output, args.format)
    kind, rows, columns = read_rows(args.output, input_format, args.hdf_key)
    print_summary(kind, rows, columns, args.sample_size)
    if args.write_tree_summary:
        write_tree_summary(args.write_tree_summary, rows, columns)


if __name__ == "__main__":
    main()
