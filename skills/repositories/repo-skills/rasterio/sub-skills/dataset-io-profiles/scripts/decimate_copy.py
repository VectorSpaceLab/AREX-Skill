#!/usr/bin/env python3
"""Copy a raster to a smaller output shape by writing the full arrays into a smaller destination.

This is a safe local-file helper adapted from Rasterio's decimation example.
It keeps the source georeferencing, shrinks width/height by a scale factor, and
writes the result without launching external viewers.

Examples
--------
python scripts/decimate_copy.py input.tif output.tif
python scripts/decimate_copy.py input.tif output.tif --scale 0.25

Use --driver if you want a different output format than the source driver.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import rasterio


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src", type=Path, help="Source raster path")
    parser.add_argument("dst", type=Path, help="Destination raster path")
    parser.add_argument(
        "--scale",
        type=float,
        default=0.5,
        help="Scale factor applied to width and height.",
    )
    parser.add_argument(
        "--driver",
        default=None,
        help="Optional output driver override. If omitted, the source driver is reused.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.scale <= 0:
        raise ValueError("scale must be positive")

    with rasterio.open(args.src) as src:
        width = max(1, int(round(src.width * args.scale)))
        height = max(1, int(round(src.height * args.scale)))

        profile = src.profile.copy()
        profile.update(width=width, height=height)
        if args.driver:
            profile["driver"] = args.driver

        with rasterio.open(args.dst, "w", **profile) as dst:
            for band in range(1, src.count + 1):
                dst.write(src.read(band), indexes=band)

    print(f"wrote {args.dst} at {width}x{height}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
