#!/usr/bin/env python3
"""Process a raster block-by-block using a ThreadPoolExecutor.

This is a safe windowed-I/O helper adapted from Rasterio's threaded example.
It reads and writes local files only, uses per-dataset locks, refuses to
overwrite an existing destination unless `--overwrite` is set, and does not
require any network access or viewer side effects.

Examples
--------
python scripts/windowed_copy.py input.tif output.tif
python scripts/windowed_copy.py input.tif output.tif --overwrite
python scripts/windowed_copy.py input.tif output.tif --reverse-bands -j 2
"""

from __future__ import annotations

import argparse
import concurrent.futures
import threading
from contextlib import nullcontext
from pathlib import Path

import rasterio
from rasterio.env import GDALVersion


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src", type=Path, help="Source raster path")
    parser.add_argument("dst", type=Path, help="Destination raster path; use --overwrite to replace an existing file.")
    parser.add_argument(
        "-j",
        "--workers",
        type=int,
        default=4,
        help="Number of worker threads.",
    )
    parser.add_argument(
        "--reverse-bands",
        action="store_true",
        help="Write bands in reverse order within each processed window.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing destination file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    src_path = args.src.resolve(strict=True)
    dst_path = args.dst.resolve(strict=False)
    if src_path == dst_path:
        raise SystemExit("src and dst refer to the same file")
    if args.dst.exists() and not args.overwrite:
        raise SystemExit(f"{args.dst} already exists; use --overwrite to replace it")
    gdal_at_least_3_11 = GDALVersion.runtime().at_least("3.11")

    with rasterio.open(
        src_path,
        thread_safe=gdal_at_least_3_11,
    ) as src:
        profile = src.profile.copy()
        profile.update(blockxsize=128, blockysize=128, tiled=True, driver="GTiff")

        with rasterio.open(dst_path, "w", **profile) as dst:
            windows = [window for _, window in dst.block_windows(1)]
            read_lock = threading.Lock() if not gdal_at_least_3_11 else nullcontext()
            write_lock = threading.Lock()

            def process(window):
                with read_lock:
                    data = src.read(window=window)
                if args.reverse_bands and data.ndim == 3:
                    data = data[::-1]
                with write_lock:
                    dst.write(data, window=window)

            with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
                list(executor.map(process, windows))

    print(f"wrote {dst_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
