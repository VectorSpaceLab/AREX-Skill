#!/usr/bin/env python3
"""Rasterize a GeoJSON geometry, feature, or feature collection to a GeoTIFF.

This helper keeps the workflow small and explicit: users provide output size,
CRS, transform, and invalid-shape handling instead of relying on hidden
repository fixtures.

Examples
--------
python scripts/rasterize_geometry.py geometry.json output.tif --width 10 --height 10
python scripts/rasterize_geometry.py features.json output.tif --value-property burn --all-touched
python scripts/rasterize_geometry.py geometry.json output.tif --no-skip-invalid
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import rasterio
from affine import Affine
from rasterio.features import rasterize


def parse_transform(text: str) -> Affine:
    values = [float(part.strip()) for part in text.split(",") if part.strip()]
    if len(values) != 6:
        raise argparse.ArgumentTypeError("transform must contain six comma-separated affine coefficients")
    return Affine(*values)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("geojson", type=Path, help="Input GeoJSON geometry, feature, or feature collection")
    parser.add_argument("dst", type=Path, help="Output GeoTIFF path")
    parser.add_argument("--width", type=int, default=10, help="Output width in pixels")
    parser.add_argument("--height", type=int, default=10, help="Output height in pixels")
    parser.add_argument("--crs", default="EPSG:4326", help="Output CRS")
    parser.add_argument("--transform", type=parse_transform, default=Affine.identity(), help="Six comma-separated affine coefficients")
    parser.add_argument("--fill", type=float, default=0, help="Fill value outside shapes")
    parser.add_argument("--default-value", type=float, default=1, help="Value burned when no property is selected")
    parser.add_argument("--value-property", default=None, help="Feature property to burn instead of --default-value")
    parser.add_argument("--dtype", default="uint8", help="Output raster dtype")
    parser.add_argument("--nodata", type=float, default=None, help="Optional output nodata value")
    parser.add_argument("--all-touched", action="store_true", help="Burn all pixels touched by shapes")
    parser.add_argument(
        "--skip-invalid",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Skip invalid shapes by default; use --no-skip-invalid to fail fast.",
    )
    return parser.parse_args()


def feature_pairs(obj: dict, value_property: str | None, default_value: float) -> Iterable[tuple[dict, float]]:
    obj_type = obj.get("type")
    if obj_type == "FeatureCollection":
        for feature in obj.get("features", []):
            if not feature.get("geometry"):
                continue
            value = feature.get("properties", {}).get(value_property, default_value) if value_property else default_value
            yield feature["geometry"], value
    elif obj_type == "Feature":
        value = obj.get("properties", {}).get(value_property, default_value) if value_property else default_value
        yield obj["geometry"], value
    else:
        yield obj, default_value


def main() -> int:
    args = parse_args()
    geojson = json.loads(args.geojson.read_text())
    pairs = list(feature_pairs(geojson, args.value_property, args.default_value))
    if not pairs:
        raise ValueError("no rasterizable geometries found")

    image = rasterize(
        pairs,
        out_shape=(args.height, args.width),
        transform=args.transform,
        fill=args.fill,
        all_touched=args.all_touched,
        dtype=args.dtype,
        skip_invalid=args.skip_invalid,
    )

    profile = {
        "driver": "GTiff",
        "width": args.width,
        "height": args.height,
        "count": 1,
        "dtype": args.dtype,
        "crs": args.crs,
        "transform": args.transform,
    }
    if args.nodata is not None:
        profile["nodata"] = args.nodata

    with rasterio.open(args.dst, "w", **profile) as dst:
        dst.write(image, 1)

    print(f"wrote {args.dst} sum={float(image.sum())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
