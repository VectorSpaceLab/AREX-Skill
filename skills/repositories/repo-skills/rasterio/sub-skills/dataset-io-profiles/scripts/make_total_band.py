#!/usr/bin/env python3
"""Average selected bands from a raster and write a one-band output.

This is a safe, local-file helper adapted from Rasterio's averaging example.
It does not open viewers or use network resources.

Examples
--------
python scripts/make_total_band.py input.tif output.tif
python scripts/make_total_band.py input.tif output.tif --bands 1 2 3 --dtype uint8
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import rasterio


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src", type=Path, help="Source raster path")
    parser.add_argument("dst", type=Path, help="Destination raster path")
    parser.add_argument(
        "--bands",
        nargs="+",
        type=int,
        default=[1, 2, 3],
        help="1-based band indexes to average.",
    )
    parser.add_argument(
        "--dtype",
        default="uint8",
        help="Output dtype. Defaults to uint8.",
    )
    parser.add_argument(
        "--compress",
        default="lzw",
        help="Compression to store in the destination profile.",
    )
    parser.add_argument(
        "--driver",
        default=None,
        help="Optional output driver override. If omitted, the source driver is reused.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    with rasterio.open(args.src) as src:
        if any(b < 1 or b > src.count for b in args.bands):
            raise ValueError(f"band indexes must be between 1 and {src.count}")

        arrays = [src.read(b).astype(np.float32) for b in args.bands]
        total = np.mean(np.stack(arrays, axis=0), axis=0)

        profile = src.profile.copy()
        profile.update(
            count=1,
            dtype=args.dtype,
            compress=args.compress,
        )
        if args.driver:
            profile["driver"] = args.driver

        out = total.astype(args.dtype)
        with rasterio.open(args.dst, "w", **profile) as dst:
            dst.write(out, 1)

    print(f"wrote {args.dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
