#!/usr/bin/env python3
"""Safe Rasterio install smoke check.

This helper is intentionally repo-independent: it can run from any current
working directory, imports the installed Rasterio package, optionally inspects a
user-supplied raster, creates a tiny temporary GeoTIFF round-trip when no input
is supplied, and can optionally run `rio --help`.

Examples
--------
python scripts/check_install.py
python scripts/check_install.py --run-cli
python scripts/check_install.py --input /path/to/data.tif
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        help="Optional raster to inspect instead of creating a temporary round-trip.",
    )
    parser.add_argument(
        "--run-cli",
        action="store_true",
        help="Also run `rio --help` as a CLI smoke check.",
    )
    return parser.parse_args()


def inspect_input(path: Path) -> None:
    with rasterio.open(path) as src:
        print(f"input={path}")
        print(f"shape={src.shape} count={src.count} driver={src.driver}")
        print(f"crs={src.crs}")
        print(f"dtype={src.dtypes}")


def roundtrip_temp_file() -> None:
    array = np.arange(9, dtype=np.uint8).reshape(3, 3)
    profile = {
        "driver": "GTiff",
        "height": 3,
        "width": 3,
        "count": 1,
        "dtype": array.dtype,
        "crs": "EPSG:4326",
        "transform": from_origin(0.0, 3.0, 1.0, 1.0),
        "nodata": 0,
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        dst_path = Path(tmpdir) / "smoke.tif"
        with rasterio.open(dst_path, "w", **profile) as dst:
            dst.write(array, 1)

        with rasterio.open(dst_path) as src:
            data = src.read(1)
            print(f"roundtrip={dst_path.name}")
            print(f"shape={src.shape} count={src.count} driver={src.driver}")
            print(f"crs={src.crs}")
            print(f"sum={int(data.sum())}")


def run_cli_help() -> None:
    completed = subprocess.run(
        ["rio", "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    first_line = completed.stdout.splitlines()[0] if completed.stdout else ""
    print(f"rio-help={first_line}")


def main() -> int:
    args = parse_args()

    print(f"rasterio={rasterio.__version__}")
    print(f"gdal={rasterio.__gdal_version__}")
    print(f"proj={rasterio.__proj_version__}")

    if args.input:
        inspect_input(args.input)
    else:
        roundtrip_temp_file()

    if args.run_cli:
        try:
            run_cli_help()
        except FileNotFoundError:
            print("rio-cli-missing=rio command not found", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
