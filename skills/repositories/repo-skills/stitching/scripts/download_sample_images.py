#!/usr/bin/env python3
"""Download the public sample images used by stitching's native tests.

This helper is explicit and safe by default: it only downloads when given a
`--dest` directory. It does not run on import. Use it when you want the public
fixture set that backs the repository's image-backed examples and tests.

Example:
  python scripts/download_sample_images.py --dest ./sample-images
  python scripts/download_sample_images.py --dest ./sample-images --list
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from urllib.parse import urlparse
from pathlib import Path

SAMPLE_URLS = [
    "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/stitching/s1.jpg",
    "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/stitching/s2.jpg",
    "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/stitching/boat1.jpg",
    "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/stitching/boat2.jpg",
    "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/stitching/boat3.jpg",
    "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/stitching/boat4.jpg",
    "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/stitching/boat5.jpg",
    "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/stitching/boat6.jpg",
    "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/stitching/budapest1.jpg",
    "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/stitching/budapest2.jpg",
    "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/stitching/budapest3.jpg",
    "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/stitching/budapest4.jpg",
    "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/stitching/budapest5.jpg",
    "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/stitching/budapest6.jpg",
    "https://raw.githubusercontent.com/lukasalexanderweber/stitching_tutorial/master/imgs/weir_1.jpg",
    "https://raw.githubusercontent.com/lukasalexanderweber/stitching_tutorial/master/imgs/weir_2.jpg",
    "https://raw.githubusercontent.com/lukasalexanderweber/stitching_tutorial/master/imgs/weir_3.jpg",
    "https://raw.githubusercontent.com/lukasalexanderweber/stitching_tutorial/master/imgs/weir_noise.jpg",
    "https://raw.githubusercontent.com/lukasalexanderweber/stitching_tutorial/master/imgs/barcode1.png",
    "https://raw.githubusercontent.com/lukasalexanderweber/stitching_tutorial/master/imgs/barcode2.png",
    "https://raw.githubusercontent.com/lukasalexanderweber/stitching_tutorial/master/imgs/mask1.png",
    "https://raw.githubusercontent.com/lukasalexanderweber/stitching_tutorial/master/imgs/mask2.png",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dest",
        type=Path,
        required=True,
        help="Destination directory for the downloaded sample images.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List the public URLs without downloading them.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing files in the destination directory.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional maximum number of URLs to process.",
    )
    return parser.parse_args()


def download(url: str, dest: Path, overwrite: bool) -> dict:
    filename = os.path.basename(urlparse(url).path)
    target = dest / filename
    if target.exists() and not overwrite:
        return {"file": filename, "status": "exists"}

    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read()
    target.write_bytes(data)
    return {"file": filename, "status": "downloaded", "bytes": len(data)}


def main() -> int:
    args = parse_args()
    urls = SAMPLE_URLS[: args.limit or None]

    if args.list:
        print(json.dumps({"count": len(urls), "urls": urls}, indent=2))
        return 0

    args.dest.mkdir(parents=True, exist_ok=True)
    results = [download(url, args.dest, args.overwrite) for url in urls]
    print(json.dumps({"count": len(results), "dest": str(args.dest), "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
