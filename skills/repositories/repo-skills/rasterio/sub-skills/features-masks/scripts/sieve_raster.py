#!/usr/bin/env python3
"""Sieve small regions from one raster band and write a one-band output.

Examples
--------
python scripts/sieve_raster.py input.tif output.tif --size 800
python scripts/sieve_raster.py input.tif output.tif --band 1 --connectivity 8
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import sieve


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src", type=Path, help="Source raster path")
    parser.add_argument("dst", type=Path, help="Destination raster path")
    parser.add_argument("--band", type=int, default=1, help="1-based band index to sieve")
    parser.add_argument("--size", type=int, required=True, help="Minimum region size to preserve")
    parser.add_argument("--connectivity", type=int, choices=[4, 8], default=4, help="Pixel connectivity")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with rasterio.open(args.src) as src:
        image = src.read(args.band)
        out = np.zeros(src.shape, dtype=image.dtype)
        result = sieve(image, size=args.size, out=out, connectivity=args.connectivity)
        profile = src.profile.copy()
        profile.update(count=1, dtype=result.dtype)
        with rasterio.open(args.dst, "w", **profile) as dst:
            dst.write(result, 1)

    print(f"wrote {args.dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
