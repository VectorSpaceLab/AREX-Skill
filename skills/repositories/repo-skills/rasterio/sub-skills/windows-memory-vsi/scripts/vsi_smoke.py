#!/usr/bin/env python3
"""Open a Rasterio path or VSI-style URI and print a compact summary.

Examples
--------
python scripts/vsi_smoke.py /path/to/input.tif
python scripts/vsi_smoke.py file:///path/to/input.tif
python scripts/vsi_smoke.py 'zip://archive.zip!member.tif'
"""

from __future__ import annotations

import argparse

import rasterio


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("uri", help="Raster path or URI, such as /path/to/input.tif, file:///path/to/input.tif, or zip://archive.zip!member.tif")
    parser.add_argument("--band", type=int, default=None, help="Optional band index to read for a sum check.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with rasterio.open(args.uri) as src:
        print(f"name={src.name}")
        print(f"driver={src.driver} shape={src.shape} count={src.count}")
        print(f"crs={src.crs}")
        if args.band is not None:
            data = src.read(args.band)
            print(f"band={args.band} dtype={data.dtype} sum={float(data.sum())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
