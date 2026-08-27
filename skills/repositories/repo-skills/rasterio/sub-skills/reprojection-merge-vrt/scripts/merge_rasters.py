#!/usr/bin/env python3
"""Merge local rasters into a single GeoTIFF mosaic.

This helper wraps rasterio.merge.merge for local files. It rejects missing
sources, in-place output paths, and accidental destination overwrite unless
--overwrite is supplied. Use WarpedVRT or reprojected intermediates first when
sources have different CRS values or rotated/flipped transforms.

Examples
--------
python scripts/merge_rasters.py a.tif b.tif --output mosaic.tif
python scripts/merge_rasters.py a.tif b.tif --output mosaic.tif --method last --overwrite
"""

from __future__ import annotations

import argparse
from contextlib import ExitStack
from pathlib import Path

import rasterio
from rasterio.enums import Resampling
from rasterio.merge import merge


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
    parser.add_argument("sources", nargs="+", type=Path, help="Existing local source raster paths")
    parser.add_argument("--output", required=True, type=Path, help="Destination GeoTIFF path")
    parser.add_argument(
        "--method",
        default="first",
        choices=["first", "last", "min", "max", "sum", "count"],
        help="Overlap merge method",
    )
    parser.add_argument(
        "--resampling",
        type=parse_resampling,
        default=Resampling.nearest,
        help="Rasterio Resampling method name, such as nearest, bilinear, cubic, or average",
    )
    parser.add_argument("--nodata", type=float, default=None, help="Optional nodata value for output")
    parser.add_argument("--dtype", default=None, help="Optional output dtype")
    parser.add_argument(
        "--bounds",
        nargs=4,
        type=float,
        metavar=("LEFT", "BOTTOM", "RIGHT", "TOP"),
        help="Optional output bounds in the source CRS",
    )
    parser.add_argument(
        "--res",
        nargs="+",
        type=float,
        metavar="RES",
        help="Optional output resolution: one value for square pixels or two values for x/y",
    )
    parser.add_argument(
        "--target-aligned-pixels",
        action="store_true",
        help="Align output bounds to integer multiples of the chosen resolution",
    )
    parser.add_argument(
        "--use-highest-res",
        action="store_true",
        help="Use the finest source resolution instead of the first source resolution",
    )
    parser.add_argument(
        "--mem-limit",
        type=int,
        default=64,
        help="Chunking memory limit in MB when writing the destination",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing destination file; never allows in-place source overwrite",
    )
    return parser.parse_args()


def resolved(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def normalize_resolution(values: list[float] | None) -> float | tuple[float, float] | None:
    if values is None:
        return None
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return (values[0], values[1])
    raise SystemExit("--res accepts one value or two values")


def main() -> int:
    args = parse_args()
    source_paths = [resolved(path) for path in args.sources]
    output_path = resolved(args.output)

    for original, path in zip(args.sources, source_paths):
        if not path.exists():
            raise SystemExit(f"source raster does not exist: {original}")
    if output_path in source_paths:
        raise SystemExit("refusing to overwrite a source raster; choose a different --output path")
    if not output_path.parent.exists():
        raise SystemExit(f"destination directory does not exist: {args.output.parent}")
    if output_path.exists() and not args.overwrite:
        raise SystemExit(f"destination already exists (use --overwrite to replace): {args.output}")
    if args.mem_limit <= 0:
        raise SystemExit("--mem-limit must be a positive integer MB value")

    res = normalize_resolution(args.res)
    if res is not None:
        if isinstance(res, tuple):
            if res[0] <= 0 or res[1] <= 0:
                raise SystemExit("--res values must be positive")
        elif res <= 0:
            raise SystemExit("--res must be positive")
    if args.bounds is not None:
        left, bottom, right, top = args.bounds
        if left >= right or bottom >= top:
            raise SystemExit("--bounds must satisfy LEFT < RIGHT and BOTTOM < TOP")

    with ExitStack() as stack:
        datasets = [stack.enter_context(rasterio.open(path)) for path in source_paths]
        first = datasets[0]
        for dataset in datasets[1:]:
            if dataset.crs != first.crs:
                raise SystemExit(
                    f"CRS mismatch: {dataset.name} has {dataset.crs}, expected {first.crs}; "
                    "use WarpedVRT or reproject first"
                )
            if dataset.count != first.count:
                raise SystemExit(
                    f"band-count mismatch: {dataset.name} has {dataset.count}, expected {first.count}"
                )
            if dataset.dtypes != first.dtypes:
                raise SystemExit(
                    f"dtype mismatch: {dataset.name} has {dataset.dtypes}, expected {first.dtypes}"
                )
            transform = dataset.transform
            if not transform.is_rectilinear or transform.a < 0 or transform.e > 0:
                raise SystemExit(
                    f"unsupported transform on {dataset.name}; rotated, flipped, or upside-down rasters cannot be merged"
                )

        merge_nodata = args.nodata if args.nodata is not None else first.nodata
        merge(
            datasets,
            bounds=tuple(args.bounds) if args.bounds else None,
            res=res,
            method=args.method,
            resampling=args.resampling,
            nodata=merge_nodata,
            dtype=args.dtype,
            target_aligned_pixels=args.target_aligned_pixels,
            mem_limit=args.mem_limit,
            use_highest_res=args.use_highest_res,
            dst_path=output_path,
            dst_kwds={"driver": "GTiff"},
        )

    with rasterio.open(output_path) as dst:
        print(
            f"wrote {output_path} shape=({dst.count}, {dst.height}, {dst.width}) "
            f"method={args.method} crs={dst.crs}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
