#!/usr/bin/env python3
"""Run a deterministic Modin taxi-style CSV/groupby smoke and validate with pandas."""
from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path


COLUMNS = [
    "trip_id",
    "pickup_datetime",
    "dropoff_datetime",
    "passenger_count",
    "trip_distance",
    "total_amount",
    "cab_type",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", help="Optional CSV with taxi-like columns.")
    parser.add_argument("--engine", choices=("Python", "Ray", "Dask"), default="Python")
    parser.add_argument("--cpus", type=int, default=2)
    parser.add_argument("--print-results", action="store_true")
    return parser.parse_args()


def configure(engine: str, cpus: int) -> None:
    if cpus < 1:
        raise SystemExit("--cpus must be positive")
    os.environ.pop("MODIN_BACKEND", None)
    os.environ["MODIN_ENGINE"] = engine
    os.environ.setdefault("MODIN_CPUS", str(cpus))


def write_fixture(tmp: Path) -> Path:
    path = tmp / "taxi_sample.csv"
    path.write_text(
        "trip_id,pickup_datetime,dropoff_datetime,passenger_count,trip_distance,total_amount,cab_type\n"
        "1,2024-01-01 00:00:00,2024-01-01 00:10:00,1,2.0,12.0,yellow\n"
        "2,2024-01-01 00:05:00,2024-01-01 00:20:00,2,3.5,20.0,green\n"
        "3,2024-01-01 00:30:00,2024-01-01 00:40:00,1,1.5,10.0,yellow\n"
        "4,2024-01-01 01:00:00,2024-01-01 01:30:00,3,8.0,44.0,green\n",
        encoding="utf-8",
    )
    return path


def compute_pandas(path: Path):
    import pandas

    df = pandas.read_csv(path, parse_dates=["pickup_datetime", "dropoff_datetime"])
    df["duration_min"] = (df["dropoff_datetime"] - df["pickup_datetime"]).dt.total_seconds() / 60
    filtered = df[(df["passenger_count"] > 0) & (df["trip_distance"] > 0)]
    result = (
        filtered.assign(fare_per_mile=filtered["total_amount"] / filtered["trip_distance"])
        .groupby("cab_type", sort=True)
        .agg(trips=("trip_id", "count"), total_amount=("total_amount", "sum"), mean_duration=("duration_min", "mean"))
        .sort_index()
    )
    return result


def compute_modin(path: Path):
    import modin.pandas as pd

    df = pd.read_csv(path, parse_dates=["pickup_datetime", "dropoff_datetime"])
    df["duration_min"] = (df["dropoff_datetime"] - df["pickup_datetime"]).dt.total_seconds() / 60
    filtered = df[(df["passenger_count"] > 0) & (df["trip_distance"] > 0)]
    result = (
        filtered.assign(fare_per_mile=filtered["total_amount"] / filtered["trip_distance"])
        .groupby("cab_type", sort=True)
        .agg(trips=("trip_id", "count"), total_amount=("total_amount", "sum"), mean_duration=("duration_min", "mean"))
        .sort_index()
    )
    return result.modin.to_pandas()


def run(path: Path, print_results: bool) -> None:
    import pandas

    missing = set(COLUMNS) - set(pandas.read_csv(path, nrows=0).columns)
    if missing:
        raise SystemExit(f"CSV is missing required columns: {sorted(missing)}")
    expected = compute_pandas(path)
    actual = compute_modin(path)
    pandas.testing.assert_frame_equal(actual, expected, check_dtype=False, rtol=1e-12, atol=1e-12)
    if print_results:
        print(actual)
    print(f"OK: validated {len(actual)} taxi groupby rows from {path}")


def main() -> int:
    args = parse_args()
    configure(args.engine, args.cpus)
    if args.csv:
        run(Path(args.csv), args.print_results)
    else:
        with tempfile.TemporaryDirectory(prefix="modin-taxi-smoke-") as tmpdir:
            run(write_fixture(Path(tmpdir)), args.print_results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
