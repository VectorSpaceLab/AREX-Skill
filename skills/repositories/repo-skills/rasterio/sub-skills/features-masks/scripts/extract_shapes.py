#!/usr/bin/env python3
"""Extract a bounded GeoJSON-like FeatureCollection from a raster band.

The helper prints at most --limit features by default to avoid accidentally
streaming huge rasters to the terminal.

Examples
--------
python scripts/extract_shapes.py input.tif --band 1 --limit 5
python scripts/extract_shapes.py input.tif --band 1 --connectivity 8 --limit 20 > shapes.json
python scripts/extract_shapes.py input.tif --valid-only --limit 20 > shapes.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import shapes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src", type=Path, help="Source raster path")
    parser.add_argument("--band", type=int, default=1, help="1-based band index to extract")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of features to output; 0 means no limit")
    parser.add_argument(
        "--connectivity",
        type=int,
        choices=[4, 8],
        default=4,
        help="Pixel connectivity used to group neighboring pixels into shapes.",
    )
    parser.add_argument(
        "--valid-only",
        action="store_true",
        help="Use the dataset band mask so nodata pixels are excluded.",
    )
    parser.add_argument(
        "--pixel-coords",
        action="store_true",
        help="Use pixel coordinates instead of the dataset transform.",
    )
    return parser.parse_args()


def scalar(value):
    if isinstance(value, np.generic):
        return value.item()
    return value


def main() -> int:
    args = parse_args()
    features = []
    with rasterio.open(args.src) as src:
        image = src.read(args.band)
        mask = src.read_masks(args.band) if args.valid_only else None
        transform = None if args.pixel_coords else src.transform
        iterator = shapes(image, mask=mask, transform=transform, connectivity=args.connectivity)
        for idx, (geom, value) in enumerate(iterator):
            if args.limit and idx >= args.limit:
                break
            features.append(
                {
                    "type": "Feature",
                    "properties": {"value": scalar(value), "band": args.band},
                    "geometry": geom,
                }
            )

    json.dump({"type": "FeatureCollection", "features": features}, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
