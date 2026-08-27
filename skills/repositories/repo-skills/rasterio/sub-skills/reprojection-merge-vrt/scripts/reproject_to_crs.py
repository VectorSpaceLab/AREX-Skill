#!/usr/bin/env python3
"""Reproject a local raster dataset to a target CRS.

This helper uses Rasterio's calculate_default_transform + reproject pattern and
keeps all work local and deterministic. Existing outputs are not overwritten
unless --overwrite is supplied, and in-place source replacement is rejected.

Examples
--------
python scripts/reproject_to_crs.py input.tif output.tif --dst-crs EPSG:4326
python scripts/reproject_to_crs.py input.tif output.tif --dst-crs EPSG:3857 --resampling bilinear --overwrite
"""

from __future__ import annotations

import argparse
from pathlib import Path

import rasterio
from rasterio.enums import Resampling
from rasterio.warp import calculate_default_transform, reproject


def parse_resampling(name: str) -> Resampling:
    try:
        return Resampling[name]
    except KeyError as exc:
        choices = ", ".join(sorted(item.name for item in Resampling))
        raise argparse.ArgumentTypeError(
            f"unknown resampling {name!r}; choose one of: {choices}"
        ) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src", type=Path, help="Existing local source raster path")
    parser.add_argument("dst", type=Path, help="Destination raster path")
    parser.add_argument("--dst-crs", default="EPSG:4326", help="Destination CRS")
    parser.add_argument(
        "--resampling",
        type=parse_resampling,
        default=Resampling.nearest,
        help="Rasterio Resampling method name, such as nearest, bilinear, cubic, or average",
    )
    parser.add_argument(
        "--driver",
        default="GTiff",
        help="Output driver name, such as GTiff",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing destination file; never allows in-place source overwrite",
    )
    return parser.parse_args()


def resolved(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def main() -> int:
    args = parse_args()
    src_path = resolved(args.src)
    dst_path = resolved(args.dst)

    if not src_path.exists():
        raise SystemExit(f"source raster does not exist: {args.src}")
    if src_path == dst_path:
        raise SystemExit("refusing to reproject in place; choose a different destination path")
    if not dst_path.parent.exists():
        raise SystemExit(f"destination directory does not exist: {args.dst.parent}")
    if dst_path.exists() and not args.overwrite:
        raise SystemExit(f"destination already exists (use --overwrite to replace): {args.dst}")

    with rasterio.open(src_path) as src:
        if src.crs is None:
            raise SystemExit("source raster has no CRS; set/repair it before reprojection")

        transform, width, height = calculate_default_transform(
            src.crs,
            args.dst_crs,
            src.width,
            src.height,
            *src.bounds,
        )
        profile = src.profile.copy()
        profile.update(
            driver=args.driver,
            crs=args.dst_crs,
            transform=transform,
            width=width,
            height=height,
        )

        with rasterio.open(dst_path, "w", **profile) as dst:
            for idx in src.indexes:
                reproject(
                    source=rasterio.band(src, idx),
                    destination=rasterio.band(dst, idx),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    src_nodata=src.nodata,
                    dst_transform=transform,
                    dst_crs=args.dst_crs,
                    dst_nodata=src.nodata,
                    resampling=args.resampling,
                )

    print(f"wrote {dst_path} width={width} height={height} dst_crs={args.dst_crs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
