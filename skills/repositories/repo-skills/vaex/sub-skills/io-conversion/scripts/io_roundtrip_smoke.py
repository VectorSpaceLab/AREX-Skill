#!/usr/bin/env python3
"""Run tiny local Vaex IO roundtrip checks.

The script creates a small in-memory Vaex DataFrame, exports it to selected local
formats, reopens each output with Vaex, and validates row counts, column names,
and simple aggregates. It also checks Pandas and Arrow table handoffs. It never
uses network paths or repository checkout files.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Optional


DEFAULT_FORMATS = ["hdf5", "arrow", "parquet", "csv"]
FORMAT_TO_SUFFIX = {
    "hdf5": ".hdf5",
    "arrow": ".arrow",
    "parquet": ".parquet",
    "feather": ".feather",
    "csv": ".csv",
}


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create tiny local Vaex exports and validate open/roundtrip behavior."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for generated files. Defaults to a new temporary directory that is kept for inspection.",
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=sorted(FORMAT_TO_SUFFIX),
        default=DEFAULT_FORMATS,
        help="Formats to export and reopen. Default: %(default)s.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing this script's expected output files inside --output-dir.",
    )
    parser.add_argument(
        "--allow-format-skips",
        action="store_true",
        help="Report per-format failures as skipped instead of making the whole script fail.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON only.",
    )
    return parser.parse_args(argv)


def ensure_local_output_dir(path: Optional[Path]) -> Path:
    if path is None:
        return Path(tempfile.mkdtemp(prefix="vaex-io-roundtrip-"))
    path = path.expanduser().resolve()
    if "://" in str(path):
        raise SystemExit("Refusing remote output directory; use a local path.")
    path.mkdir(parents=True, exist_ok=True)
    return path


def assert_expected(df, expected_columns: List[str], expected_len: int, expected_sum: float) -> None:
    columns = df.get_column_names()
    if columns != expected_columns:
        raise AssertionError(f"columns differ: {columns!r} != {expected_columns!r}")
    if len(df) != expected_len:
        raise AssertionError(f"row count differs: {len(df)!r} != {expected_len!r}")
    got = float(df.value.sum())
    if not math.isclose(got, expected_sum, rel_tol=0, abs_tol=1e-9):
        raise AssertionError(f"value sum differs: {got!r} != {expected_sum!r}")


def export_one(df, fmt: str, path: Path) -> None:
    if fmt == "hdf5":
        df.export_hdf5(str(path))
    elif fmt == "csv":
        df.export_csv(str(path), index=False, chunk_size=2)
    else:
        df.export(str(path), chunk_size=2)


def maybe_remove_existing(paths: Iterable[Path], overwrite: bool) -> None:
    for path in paths:
        if path.exists():
            if not overwrite:
                raise SystemExit(
                    f"Refusing to overwrite existing {path}; pass --overwrite or choose another --output-dir."
                )
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()


def run_smoke(args: argparse.Namespace) -> Dict[str, object]:
    import pandas as pd
    import pyarrow as pa
    import vaex

    output_dir = ensure_local_output_dir(args.output_dir)
    expected_columns = ["id", "value", "label"]
    expected_len = 4
    expected_sum = 22.5

    expected_paths = [output_dir / f"tiny{FORMAT_TO_SUFFIX[fmt]}" for fmt in args.formats]
    maybe_remove_existing(expected_paths, args.overwrite)

    df = vaex.from_arrays(
        id=[1, 2, 3, 4],
        value=[10.0, -2.5, 7.0, 8.0],
        label=["a", "b", "a", "c"],
    )
    assert_expected(df, expected_columns, expected_len, expected_sum)

    results: Dict[str, object] = {
        "output_dir": str(output_dir),
        "vaex_version": getattr(vaex, "__version__", "unknown"),
        "formats": {},
        "handoffs": {},
    }

    for fmt, path in zip(args.formats, expected_paths):
        try:
            export_one(df, fmt, path)
            reopened = vaex.open(str(path))
            assert_expected(reopened, expected_columns, expected_len, expected_sum)
            results["formats"][fmt] = {
                "status": "passed",
                "path": str(path),
                "size_bytes": path.stat().st_size,
            }
        except Exception as exc:  # noqa: BLE001 - user-facing smoke summary
            status = "skipped" if args.allow_format_skips else "failed"
            results["formats"][fmt] = {
                "status": status,
                "path": str(path),
                "error": f"{type(exc).__name__}: {exc}",
            }
            if not args.allow_format_skips:
                raise

    # Pandas -> Vaex handoff.
    pdf = pd.DataFrame({"id": [5, 6], "value": [1.5, 2.5], "label": ["p", "q"]})
    df_from_pandas = vaex.from_pandas(pdf, copy_index=False)
    assert_expected(df_from_pandas, expected_columns, 2, 4.0)
    results["handoffs"]["from_pandas"] = {"status": "passed", "rows": len(df_from_pandas)}

    # Vaex -> Arrow table -> Vaex handoff.
    arrow_table = df.to_arrow_table(expected_columns)
    if not isinstance(arrow_table, pa.Table):
        raise AssertionError(f"to_arrow_table returned {type(arrow_table)!r}, expected pyarrow.Table")
    df_from_arrow = vaex.from_arrow_table(arrow_table)
    assert_expected(df_from_arrow, expected_columns, expected_len, expected_sum)
    results["handoffs"]["arrow_table_roundtrip"] = {
        "status": "passed",
        "rows": arrow_table.num_rows,
        "columns": arrow_table.column_names,
    }

    return results


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        results = run_smoke(args)
        ok = all(item.get("status") in {"passed", "skipped"} for item in results["formats"].values())
        if args.json:
            print(json.dumps(results, indent=2, sort_keys=True))
        else:
            print("Vaex IO roundtrip smoke complete")
            print(json.dumps(results, indent=2, sort_keys=True))
        return 0 if ok else 1
    except Exception as exc:  # noqa: BLE001 - command-line diagnostic
        if args.json:
            print(json.dumps({"status": "failed", "error": f"{type(exc).__name__}: {exc}"}, indent=2))
        else:
            print(f"FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
