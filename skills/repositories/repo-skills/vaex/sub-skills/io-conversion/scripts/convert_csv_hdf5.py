#!/usr/bin/env python3
"""Safely convert a local CSV file to Vaex HDF5 and optionally validate it.

This is a local-only helper inspired by Vaex's public conversion behavior. It
uses installed public APIs (`vaex.open`, `vaex.from_csv`, `df.export_hdf5`) and
adds conservative overwrite/cleanup guards. It does not contact cloud storage,
TAP services, or credential providers.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def fraction_value(value: str) -> float:
    parsed = float(value)
    if not (0 < parsed <= 1):
        raise argparse.ArgumentTypeError("must be in the interval (0, 1]")
    return parsed


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a local CSV file to Vaex HDF5 with safe cleanup and validation options."
    )
    parser.add_argument("input_csv", type=Path, help="Local CSV input path. Remote URLs are refused.")
    parser.add_argument("output_hdf5", type=Path, help="Local .hdf5 output path. Remote URLs are refused.")
    parser.add_argument(
        "--columns",
        nargs="+",
        default=None,
        help="Optional exact column names to export, in output order.",
    )
    parser.add_argument(
        "--filter",
        dest="filter_expression",
        default=None,
        help="Optional Vaex filter expression to apply before export, e.g. 'amount > 0'.",
    )
    parser.add_argument("--sort", default=None, help="Optional column/expression to sort by before export.")
    parser.add_argument(
        "--fraction",
        type=fraction_value,
        default=1.0,
        help="Active fraction of rows to export, in (0, 1]. Default: %(default)s.",
    )
    parser.add_argument(
        "--chunk-size",
        type=positive_int,
        default=5_000_000,
        help="Rows per CSV/export chunk. Lower this for wide rows or memory pressure. Default: %(default)s.",
    )
    parser.add_argument(
        "--shuffle",
        action="store_true",
        help="Shuffle rows before export. Avoid this when deterministic row order is required.",
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Run Vaex categorize/downcast optimization before export. May change dtypes.",
    )
    parser.add_argument(
        "--categorize",
        action="store_true",
        help="Run df.optimize.categorize() before export.",
    )
    parser.add_argument(
        "--downcast",
        action="store_true",
        help="Run df.optimize.downcast() before export. Validate dtype/range changes afterwards.",
    )
    parser.add_argument(
        "--downcast-float",
        action="store_true",
        help="Allow float64 to float32 downcasting when --downcast or --optimize is used.",
    )
    parser.add_argument(
        "--list-columns",
        action="store_true",
        help="Print inferred input columns and exit before writing output.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Open the CSV, apply requested column/filter/sort/fraction checks, and report planned output without writing.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Reopen output and validate row count, columns, and simple numeric aggregates after conversion.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing output file. Without this, existing output is refused.",
    )
    parser.add_argument(
        "--no-delete",
        action="store_true",
        help="Keep the temporary output file if conversion fails.",
    )
    parser.add_argument(
        "--progress",
        dest="progress",
        action="store_true",
        default=False,
        help="Enable Vaex progress output. Default is disabled for log-friendly runs.",
    )
    parser.add_argument(
        "--no-progress",
        dest="progress",
        action="store_false",
        help="Disable Vaex progress output explicitly.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON only.",
    )
    return parser.parse_args(argv)


def reject_remote(path: Path, label: str) -> Path:
    raw = str(path)
    if "://" in raw or raw.startswith("tap+"):
        raise SystemExit(f"Refusing remote {label} path {raw!r}; this helper is local-only.")
    return path.expanduser().resolve()


def inspect_and_transform(args: argparse.Namespace):
    import vaex

    # `vaex.open(csv)` uses lazy Arrow-backed CSV for Vaex 4.14+ and avoids
    # loading the full file merely to inspect schema or apply lazy transforms.
    df = vaex.open(str(args.input_csv))
    columns = df.get_column_names()

    if args.columns:
        missing = [name for name in args.columns if name not in columns]
        if missing:
            raise ValueError(
                f"Missing requested columns {missing!r}. Available columns: {columns!r}"
            )
        df = df[args.columns]
        columns = df.get_column_names()

    if args.fraction != 1.0:
        df.set_active_fraction(args.fraction)
    if args.filter_expression:
        df = df.filter(args.filter_expression)
    if args.sort:
        df = df.sort(args.sort)
    if args.shuffle:
        df = df.shuffle()
    if args.optimize or args.categorize:
        df = df.optimize.categorize()
    if args.optimize or args.downcast:
        df = df.optimize.downcast(float64=args.optimize or args.downcast_float)
    columns = df.get_column_names()
    return df, columns


def numeric_aggregates(df, columns: List[str]) -> Dict[str, Dict[str, Any]]:
    aggregates: Dict[str, Dict[str, Any]] = {}
    for name in columns:
        try:
            dtype_text = str(df.data_type(name))
        except Exception:  # noqa: BLE001 - diagnostic helper
            dtype_text = "unknown"
        if any(token in dtype_text.lower() for token in ["int", "float", "double"]):
            try:
                aggregates[name] = {
                    "dtype": dtype_text,
                    "count": int(df[name].count()),
                    "sum": float(df[name].sum()),
                }
            except Exception as exc:  # noqa: BLE001 - keep diagnostic non-fatal
                aggregates[name] = {"dtype": dtype_text, "error": f"{type(exc).__name__}: {exc}"}
    return aggregates


def validate_output(output_hdf5: Path, expected_rows: int, expected_columns: List[str], expected_aggs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    import math
    import vaex

    reopened = vaex.open(str(output_hdf5))
    got_columns = reopened.get_column_names()
    if got_columns != expected_columns:
        raise AssertionError(f"Output columns {got_columns!r} != expected {expected_columns!r}")
    got_rows = len(reopened)
    if got_rows != expected_rows:
        raise AssertionError(f"Output rows {got_rows!r} != expected {expected_rows!r}")
    got_aggs = numeric_aggregates(reopened, got_columns)
    for name, expected in expected_aggs.items():
        if "sum" in expected and "sum" in got_aggs.get(name, {}):
            if not math.isclose(got_aggs[name]["sum"], expected["sum"], rel_tol=1e-9, abs_tol=1e-9):
                raise AssertionError(
                    f"Output aggregate sum for {name!r} {got_aggs[name]['sum']!r} != {expected['sum']!r}"
                )
    return {"rows": got_rows, "columns": got_columns, "numeric_aggregates": got_aggs}


def convert(args: argparse.Namespace) -> Dict[str, Any]:
    args.input_csv = reject_remote(args.input_csv, "input")
    args.output_hdf5 = reject_remote(args.output_hdf5, "output")
    if args.output_hdf5.suffix.lower() not in {".hdf5", ".h5"}:
        raise SystemExit("Output path should end in .hdf5 or .h5 for Vaex HDF5 conversion.")
    if not args.input_csv.exists():
        raise SystemExit(f"Input CSV does not exist: {args.input_csv}")
    if args.output_hdf5.exists() and not args.overwrite and not (args.dry_run or args.list_columns):
        raise SystemExit(f"Output exists: {args.output_hdf5}. Pass --overwrite to replace it.")

    df, columns = inspect_and_transform(args)
    rows = len(df)
    aggs = numeric_aggregates(df, columns)
    report: Dict[str, Any] = {
        "input_csv": str(args.input_csv),
        "output_hdf5": str(args.output_hdf5),
        "rows_planned": rows,
        "columns": columns,
        "numeric_aggregates": aggs,
        "filter": args.filter_expression,
        "sort": args.sort,
        "fraction": args.fraction,
        "chunk_size": args.chunk_size,
        "shuffle": args.shuffle,
        "optimize": args.optimize,
        "categorize": args.categorize,
        "downcast": args.downcast,
        "downcast_float": args.downcast_float,
    }

    if args.list_columns:
        report["status"] = "listed"
        return report
    if args.dry_run:
        report["status"] = "dry-run"
        return report

    args.output_hdf5.parent.mkdir(parents=True, exist_ok=True)
    temp_path = Path(
        tempfile.mktemp(
            prefix=f".{args.output_hdf5.name}.",
            suffix=".tmp.hdf5",
            dir=str(args.output_hdf5.parent),
        )
    )

    try:
        df.export_hdf5(
            str(temp_path),
            progress=args.progress,
            chunk_size=args.chunk_size,
        )
        if args.validate:
            validate_output(temp_path, rows, columns, aggs)
        if args.output_hdf5.exists():
            if args.output_hdf5.is_dir():
                shutil.rmtree(args.output_hdf5)
            else:
                args.output_hdf5.unlink()
        os.replace(temp_path, args.output_hdf5)
        report["status"] = "converted"
        report["bytes"] = args.output_hdf5.stat().st_size
        if args.validate:
            report["validation"] = validate_output(args.output_hdf5, rows, columns, aggs)
        return report
    except Exception:
        report["status"] = "failed"
        report["temporary_output"] = str(temp_path)
        if temp_path.exists() and not args.no_delete:
            temp_path.unlink()
            report["temporary_output_deleted"] = True
        elif temp_path.exists():
            report["temporary_output_deleted"] = False
        raise


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report = convert(args)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        elif args.list_columns:
            print("Columns:")
            for name in report["columns"]:
                print(name)
        else:
            print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # noqa: BLE001 - command-line diagnostic
        payload = {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"FAILED: {payload['error']}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
