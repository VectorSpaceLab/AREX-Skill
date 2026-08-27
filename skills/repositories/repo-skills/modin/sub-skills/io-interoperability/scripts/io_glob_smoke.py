#!/usr/bin/env python3
"""Tiny local smoke test for Modin experimental glob I/O."""
from __future__ import annotations

import argparse
import glob
import importlib.util
import os
import sys
import tempfile
from pathlib import Path
from typing import Iterable

SUPPORTED_GLOB_ENGINES = {"Ray", "Dask", "Unidist"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--engine",
        choices=("Ray", "Dask", "Unidist", "Auto"),
        default="Auto",
        help="Execution engine for experimental glob APIs. Auto leaves Ray/Dask/Unidist in place or defaults to Ray.",
    )
    parser.add_argument("--cpus", type=int, default=2, help="Set MODIN_CPUS for this process.")
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=("csv", "json", "parquet"),
        default=("csv", "json", "parquet"),
        help="Glob formats to attempt. CSV is the required baseline.",
    )
    parser.add_argument("--strict-optional", action="store_true", help="Fail if optional JSON/parquet glob checks fail instead of reporting them as skipped.")
    return parser.parse_args(argv)


def configure_environment(engine: str, cpus: int) -> str:
    if cpus <= 0:
        raise ValueError("--cpus must be positive")
    os.environ.pop("MODIN_BACKEND", None)
    os.environ.pop("MODIN_STORAGE_FORMAT", None)
    selected = os.environ.get("MODIN_ENGINE") if engine == "Auto" else engine
    if selected not in SUPPORTED_GLOB_ENGINES:
        selected = "Ray"
    os.environ["MODIN_ENGINE"] = selected
    os.environ["MODIN_CPUS"] = str(cpus)
    os.environ.setdefault("MODIN_NPARTITIONS", str(min(max(cpus, 1), 4)))
    return selected


def make_csv_parts(tmp: Path) -> list[Path]:
    rows = [[(1, "a", 10.0), (2, "b", 20.5)], [(3, "a", 30.0), (4, "b", 40.5)]]
    paths: list[Path] = []
    for idx, part_rows in enumerate(rows):
        path = tmp / f"part-{idx}.csv"
        with path.open("w", encoding="utf-8") as handle:
            handle.write("id,group,value\n")
            for row in part_rows:
                handle.write(f"{row[0]},{row[1]},{row[2]}\n")
        paths.append(path)
    return paths


def normalize_for_compare(frame):
    normalized = frame.reset_index(drop=True)
    columns = list(normalized.columns)
    if columns and len(normalized) > 0:
        normalized = normalized.sort_values(columns).reset_index(drop=True)
    return normalized


def assert_frame_equal(left, right, *, check_dtype: bool = True) -> None:
    import pandas as pandas_pd

    pandas_pd.testing.assert_frame_equal(
        normalize_for_compare(left), normalize_for_compare(right), check_dtype=check_dtype
    )


def run_csv_glob(tmp: Path) -> str:
    import pandas as pandas_pd
    import modin.experimental.pandas as mpd

    paths = make_csv_parts(tmp)
    pattern = str(tmp / "part-*.csv")
    if not glob.glob(pattern):
        raise AssertionError(f"fixture glob did not match files: {pattern}")

    expected = pandas_pd.concat([pandas_pd.read_csv(path) for path in sorted(paths)], ignore_index=True)
    actual = mpd.read_csv_glob(pattern).reset_index(drop=True).modin.to_pandas()
    assert_frame_equal(actual, expected)
    return f"csv ok ({len(expected)} rows from {len(paths)} files)"


def run_json_glob(tmp: Path) -> str:
    import pandas as pandas_pd
    import modin.experimental.pandas as mpd

    expected = pandas_pd.DataFrame({"id": [1, 2, 3, 4], "group": ["a", "b", "a", "b"], "value": [1.5, 2.5, 3.5, 4.5]})
    modin_df = mpd.DataFrame(expected)
    pattern = str(tmp / "json-part-*.json")
    modin_df.modin.to_json_glob(pattern)
    actual = mpd.read_json_glob(pattern).reset_index(drop=True).modin.to_pandas()
    assert_frame_equal(actual, expected, check_dtype=False)
    return "json glob ok"


def run_parquet_glob(tmp: Path) -> str:
    if importlib.util.find_spec("pyarrow") is None and importlib.util.find_spec("fastparquet") is None:
        raise RuntimeError("neither pyarrow nor fastparquet is installed")

    import pandas as pandas_pd
    import modin.experimental.pandas as mpd

    expected = pandas_pd.DataFrame({"id": [1, 2, 3, 4], "group": ["a", "b", "a", "b"], "value": [1.5, 2.5, 3.5, 4.5]})
    modin_df = mpd.DataFrame(expected)
    pattern = str(tmp / "parquet-part-*.parquet")
    modin_df.modin.to_parquet_glob(pattern)
    actual = mpd.read_parquet_glob(pattern).reset_index(drop=True).modin.to_pandas()
    assert_frame_equal(actual, expected, check_dtype=False)
    return "parquet glob ok"


def report_optional(name: str, exc: BaseException, strict: bool) -> str:
    if strict:
        raise exc
    return f"{name} skipped/failed optional check: {type(exc).__name__}: {exc}"


def run_selected_formats(formats: Iterable[str], strict_optional: bool) -> list[str]:
    messages: list[str] = []
    with tempfile.TemporaryDirectory(prefix="modin-io-glob-") as tmpdir:
        tmp = Path(tmpdir)
        if "csv" in formats:
            messages.append(run_csv_glob(tmp))
        if "json" in formats:
            try:
                messages.append(run_json_glob(tmp))
            except Exception as exc:
                messages.append(report_optional("json", exc, strict_optional))
        if "parquet" in formats:
            try:
                messages.append(run_parquet_glob(tmp))
            except Exception as exc:
                messages.append(report_optional("parquet", exc, strict_optional))
    return messages


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        selected_engine = configure_environment(args.engine, args.cpus)
        messages = run_selected_formats(args.formats, args.strict_optional)
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"MODIN_ENGINE={selected_engine}")
    for message in messages:
        print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
