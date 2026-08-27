#!/usr/bin/env python3
"""Tiny Koalas Spark I/O smoke check.

The script creates local in-memory data, round-trips it through Koalas/Spark
interop and one or more local file formats, and exits non-zero on failure. It
uses temporary directories and does not require repository source files.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from typing import Iterable, List, Optional

# These must be set before PySpark/Koalas import for local smoke runs.
os.environ.setdefault("PYARROW_IGNORE_TIMEZONE", "1")
os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny Koalas Spark interop and local I/O round-trip smoke check."
    )
    parser.add_argument(
        "--format",
        dest="formats",
        action="append",
        choices=("csv", "parquet"),
        help="Format to test. May be supplied more than once. Defaults to csv.",
    )
    parser.add_argument(
        "--master",
        default="local[1]",
        help="Spark master for the smoke run. Default: local[1].",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep the temporary output directory and print its path.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print extra progress information.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def make_spark(master: str):
    from pyspark.sql import SparkSession

    spark = (
        SparkSession.builder.master(master)
        .appName("koalas-io-smoke")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark


def assert_frame_values(kdf, expected_values: List[int]) -> None:
    pdf = kdf.sort_index().to_pandas()
    values = [int(v) for v in pdf["value"].tolist()]
    if values != expected_values:
        raise AssertionError(f"unexpected values: got {values}, expected {expected_values}")


def run_interop_checks(ks, spark, verbose: bool = False):
    if verbose:
        print("creating tiny Koalas DataFrame")
    kdf = ks.DataFrame(
        {"row_id": [101, 102, 103], "group": ["a", "b", "a"], "value": [10, 20, 30]}
    ).set_index("row_id")

    schema = kdf.spark.schema(index_col="row_id")
    if "row_id" not in schema.fieldNames():
        raise AssertionError("row_id missing from Spark schema when index_col is supplied")

    if verbose:
        print("checking Koalas -> Spark -> Koalas explicit-index round-trip")
    sdf = kdf.to_spark(index_col="row_id").filter("value >= 20")
    back = sdf.to_koalas(index_col="row_id")
    assert_frame_values(back, [20, 30])

    if verbose:
        print("checking DataFrame.spark.apply with explicit index_col")
    applied = kdf.spark.apply(
        lambda sdf: sdf.selectExpr("row_id", "group", "value * 2 as value"),
        index_col="row_id",
    )
    assert_frame_values(applied, [20, 40, 60])

    if verbose:
        print("checking ks.sql variable substitution")
    sql_input = kdf.reset_index()
    sql_result = ks.sql(
        "SELECT row_id, value FROM {table} WHERE value >= {minimum}",
        table=sql_input,
        minimum=20,
    )
    sql_pdf = sql_result.to_pandas().sort_values("row_id")
    values = [int(v) for v in sql_pdf["value"].tolist()]
    if values != [20, 30]:
        raise AssertionError(f"unexpected SQL values: got {values}")

    return kdf


def run_csv_roundtrip(ks, kdf, root: str, verbose: bool = False) -> None:
    path = os.path.join(root, "csv_roundtrip")
    if verbose:
        print(f"writing CSV to {path}")
    kdf.to_csv(path, num_files=1, index_col="row_id", mode="overwrite")
    actual = ks.read_csv(path, index_col="row_id")
    assert_frame_values(actual, [10, 20, 30])


def run_parquet_roundtrip(ks, kdf, root: str, verbose: bool = False) -> None:
    path = os.path.join(root, "parquet_roundtrip")
    if verbose:
        print(f"writing Parquet to {path}")
    kdf.to_parquet(path, index_col="row_id", mode="overwrite")
    actual = ks.read_parquet(path, index_col="row_id")
    assert_frame_values(actual, [10, 20, 30])


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    formats = args.formats or ["csv"]
    temp_root = tempfile.mkdtemp(prefix="koalas-io-smoke-")
    spark = None
    try:
        spark = make_spark(args.master)
        import databricks.koalas as ks

        kdf = run_interop_checks(ks, spark, verbose=args.verbose)
        for fmt in formats:
            if fmt == "csv":
                run_csv_roundtrip(ks, kdf, temp_root, verbose=args.verbose)
            elif fmt == "parquet":
                run_parquet_roundtrip(ks, kdf, temp_root, verbose=args.verbose)
            else:  # argparse should prevent this.
                raise ValueError(f"unsupported format: {fmt}")
        print("OK: Koalas Spark interop and I/O smoke checks passed for " + ", ".join(formats))
        if args.keep_temp:
            print(f"temporary output kept at: {temp_root}")
        return 0
    finally:
        if spark is not None:
            spark.stop()
        if not args.keep_temp:
            shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - command-line diagnostics
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
