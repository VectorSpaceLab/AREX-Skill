#!/usr/bin/env python3
"""Smoke-check Rasterio MemoryFile usage.

Without --source this creates a tiny in-memory GeoTIFF. With --source it reads a
local raster's bytes into a MemoryFile and opens it there.

Examples
--------
python scripts/memoryfile_smoke.py
python scripts/memoryfile_smoke.py --source input.tif
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.transform import from_origin


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Optional local raster path to load into MemoryFile.")
    return parser.parse_args()


def open_existing(path: Path) -> None:
    with MemoryFile(path.read_bytes()) as memfile:
        with memfile.open() as src:
            print(f"memoryfile-source={path}")
            print(f"driver={src.driver} shape={src.shape} count={src.count} dtype={src.dtypes}")


def create_tiny() -> None:
    data = np.arange(9, dtype=np.uint8).reshape(3, 3)
    profile = {
        "driver": "GTiff",
        "width": 3,
        "height": 3,
        "count": 1,
        "dtype": "uint8",
        "crs": "EPSG:4326",
        "transform": from_origin(0.0, 3.0, 1.0, 1.0),
    }
    with MemoryFile() as memfile:
        with memfile.open(**profile) as dst:
            dst.write(data, 1)
        with memfile.open() as src:
            print("memoryfile-source=generated")
            print(f"driver={src.driver} shape={src.shape} count={src.count} sum={int(src.read(1).sum())}")


def main() -> int:
    args = parse_args()
    if args.source:
        open_existing(args.source)
    else:
        create_tiny()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
