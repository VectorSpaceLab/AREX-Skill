#!/usr/bin/env python3
"""Tiny offline GeoTIFF/image-prep/vectorization smoke for SamGeo utilities.

Creates a temporary 5-band GeoTIFF, verifies RGB band selection with
read_image_for_sam(), writes an all-zero mask GeoTIFF, and verifies that
raster_to_vector() produces a valid empty GeoJSON FeatureCollection.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from samgeo import common


def run(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    image = out_dir / "mini-multiband.tif"
    mask = out_dir / "empty-mask.tif"
    vector = out_dir / "empty-mask.geojson"

    data = np.zeros((5, 4, 6), dtype=np.uint8)
    for band in range(data.shape[0]):
        data[band] = (band + 1) * 10

    transform = from_origin(-180, 90, 1, 1)
    with rasterio.open(
        image,
        "w",
        driver="GTiff",
        height=data.shape[1],
        width=data.shape[2],
        count=data.shape[0],
        dtype=data.dtype,
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(data)

    rgb = common.read_image_for_sam(str(image), bands=[5, 3, 1])
    assert rgb.shape == (4, 6, 3), rgb.shape
    assert int(rgb[0, 0, 0]) == 50
    assert int(rgb[0, 0, 1]) == 30
    assert int(rgb[0, 0, 2]) == 10

    zeros = np.zeros((1, 8, 8), dtype=np.uint8)
    with rasterio.open(
        mask,
        "w",
        driver="GTiff",
        height=8,
        width=8,
        count=1,
        dtype=zeros.dtype,
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(zeros)

    common.raster_to_vector(str(mask), str(vector))
    feature_collection = json.loads(vector.read_text())
    assert feature_collection["type"] == "FeatureCollection"
    assert feature_collection["features"] == []

    return {
        "image": str(image.name),
        "mask": str(mask.name),
        "vector": str(vector.name),
        "rgb_shape": list(rgb.shape),
        "empty_feature_count": len(feature_collection["features"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=None, help="Optional directory to keep generated tiny files.")
    parser.add_argument("--json", action="store_true", help="Emit JSON result.")
    args = parser.parse_args()

    if args.out_dir is None:
        with tempfile.TemporaryDirectory(prefix="samgeo-mini-") as tmp:
            result = run(Path(tmp))
    else:
        result = run(args.out_dir)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("SamGeo mini GeoTIFF roundtrip passed:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
