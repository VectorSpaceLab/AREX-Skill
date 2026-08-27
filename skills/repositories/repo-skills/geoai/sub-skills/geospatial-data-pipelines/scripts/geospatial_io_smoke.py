#!/usr/bin/env python3
"""Smoke-test GeoAI geospatial I/O on tiny local fixtures.

Safe by default:
- no network access
- no model downloads
- no training
- no destructive writes outside a temporary directory

If raster and/or vector inputs are provided, the script inspects them and
reports CRS compatibility. If one side is missing, the script creates a tiny
synthetic companion fixture in a temporary directory and exercises the local
raster/vector conversion helpers.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _parse_bbox(value: str) -> Tuple[float, float, float, float]:
    parts = [piece.strip() for piece in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError(
            "bbox must contain four comma-separated numbers: minx,miny,maxx,maxy"
        )
    try:
        coords = tuple(float(piece) for piece in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "bbox must contain four comma-separated numbers: minx,miny,maxx,maxy"
        ) from exc
    return coords  # type: ignore[return-value]


def _write_sample_raster(path: Path, *, size: int = 64, crs: str = "EPSG:4326") -> None:
    import numpy as np
    import rasterio
    from rasterio.transform import from_bounds

    data = np.zeros((1, size, size), dtype=np.uint8)
    data[0, size // 4 : 3 * size // 4, size // 4 : 3 * size // 4] = 1
    transform = from_bounds(-122.5, 37.7, -122.3, 37.9, size, size)
    profile = {
        "driver": "GTiff",
        "height": size,
        "width": size,
        "count": 1,
        "dtype": "uint8",
        "crs": crs,
        "transform": transform,
        "nodata": 0,
        "compress": "lzw",
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data)


def _write_sample_vector(path: Path, *, crs: str = "EPSG:4326") -> None:
    import geopandas as gpd
    from shapely.geometry import box

    gdf = gpd.GeoDataFrame(
        {"name": ["smoke_square"]},
        geometry=[box(-122.46, 37.74, -122.34, 37.86)],
        crs=crs,
    )
    gdf.to_file(path, driver="GeoJSON")


def _info_summary(raster_path: Path, vector_path: Path, workspace: Path) -> Dict[str, Any]:
    import geopandas as gpd
    import rasterio

    from geoai.utils.raster import get_raster_info, get_raster_resolution, raster_to_vector, vector_to_raster
    from geoai.utils.vector import get_vector_info

    raster_info = get_raster_info(str(raster_path))
    vector_info = get_vector_info(str(vector_path))

    with rasterio.open(raster_path) as src:
        raster_crs = src.crs
        raster_bounds = src.bounds
    vector_gdf = gpd.read_file(vector_path)
    vector_crs = vector_gdf.crs
    vector_bounds = tuple(vector_gdf.total_bounds.tolist())

    summary: Dict[str, Any] = {
        "raster_path": str(raster_path),
        "vector_path": str(vector_path),
        "raster_crs": str(raster_crs) if raster_crs else None,
        "vector_crs": str(vector_crs) if vector_crs else None,
        "raster_bounds": tuple(float(x) for x in raster_bounds),
        "vector_bounds": vector_bounds,
        "raster_info": raster_info,
        "vector_info": vector_info,
        "raster_shape": (int(raster_info.get("count", 0)), int(raster_info.get("height", 0)), int(raster_info.get("width", 0))),
        "raster_resolution": tuple(float(x) for x in get_raster_resolution(str(raster_path))),
        "vector_rows": int(len(vector_gdf)),
    }

    # Round-trip tests live inside the temporary working directory.
    roundtrip_raster = workspace / "vector_to_raster_roundtrip.tif"
    roundtrip_vector = workspace / "raster_to_vector_roundtrip.geojson"
    vector_to_raster(str(vector_path), output_path=str(roundtrip_raster), reference_raster=str(raster_path))
    raster_to_vector(str(raster_path), output_path=str(roundtrip_vector), simplify_tolerance=1.0)

    summary["vector_to_raster_output"] = str(roundtrip_raster)
    summary["raster_to_vector_output"] = str(roundtrip_vector)

    return summary


def _validate_pair(
    raster_path: Path,
    vector_path: Path,
    *,
    workspace: Path,
    bbox: Optional[Tuple[float, float, float, float]] = None,
    strict_crs: bool = False,
) -> Tuple[Dict[str, Any], int]:
    import geopandas as gpd
    import rasterio

    from geoai.utils.raster import clip_raster_by_bbox

    summary = _info_summary(raster_path, vector_path, workspace)
    exit_code = 0

    with rasterio.open(raster_path) as src:
        raster_crs = src.crs
    vector_gdf = gpd.read_file(vector_path)
    vector_crs = vector_gdf.crs

    if raster_crs is None:
        summary["error"] = "Raster has no CRS"
        return summary, 2
    if vector_crs is None:
        summary["error"] = "Vector has no CRS"
        return summary, 2

    crs_match = str(raster_crs) == str(vector_crs)
    summary["crs_match"] = crs_match
    if not crs_match:
        summary["warning"] = (
            f"CRS mismatch: raster={raster_crs}, vector={vector_crs}. "
            "Reproject the vector to the raster CRS before tiling or vectorizing."
        )
        if strict_crs:
            exit_code = 3

    if bbox is not None:
        clipped_path = workspace / "bbox_clip.tif"
        clip_raster_by_bbox(
            str(raster_path),
            str(clipped_path),
            list(bbox),
            bbox_type="geo",
            bbox_crs="EPSG:4326",
        )
        summary["bbox"] = bbox
        summary["clipped_path"] = str(clipped_path)

    return summary, exit_code


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke-test GeoAI raster/vector I/O and CRS alignment using tiny local fixtures.",
    )
    parser.add_argument(
        "--raster",
        type=Path,
        help="Optional raster to inspect. If omitted, a synthetic temporary raster is created.",
    )
    parser.add_argument(
        "--vector",
        type=Path,
        help="Optional vector to inspect. If omitted, a synthetic temporary vector is created.",
    )
    parser.add_argument(
        "--bbox",
        type=_parse_bbox,
        help="Optional geographic bbox to clip the raster: minx,miny,maxx,maxy (use --bbox=... when values are negative).",
    )
    parser.add_argument(
        "--strict-crs",
        action="store_true",
        help="Return a nonzero exit code when raster and vector CRS do not match.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON report instead of human-readable text.",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=64,
        help="Size of the synthetic raster side length when a fixture must be created.",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        # Import after argument parsing so --help remains dependency-light.
        import geopandas as gpd  # noqa: F401
        import rasterio  # noqa: F401
        from geoai.utils.raster import get_raster_info
        from geoai.utils.vector import get_vector_info
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"Error: could not import required geospatial dependencies: {exc}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        raster_path = args.raster
        vector_path = args.vector

        # Create synthetic fixtures as needed.
        if raster_path is None:
            raster_path = tmp / "smoke_raster.tif"
            _write_sample_raster(raster_path, size=args.size)
        if vector_path is None:
            vector_path = tmp / "smoke_vector.geojson"
            _write_sample_vector(vector_path)

        try:
            summary, exit_code = _validate_pair(
                raster_path,
                vector_path,
                workspace=tmp,
                bbox=args.bbox,
                strict_crs=args.strict_crs,
            )
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

        # Add a short, explicit report from the inspection helpers.
        try:
            summary["raster_info_keys"] = sorted(get_raster_info(str(raster_path)).keys())
            summary["vector_info_keys"] = sorted(get_vector_info(str(vector_path)).keys())
        except Exception as exc:
            print(f"Error collecting GeoAI metadata: {exc}", file=sys.stderr)
            return 1

        if args.json:
            print(json.dumps(summary, indent=2, sort_keys=True, default=str))
        else:
            print(f"Raster: {summary['raster_path']}")
            print(f"Vector: {summary['vector_path']}")
            print(f"Raster CRS: {summary.get('raster_crs')}")
            print(f"Vector CRS: {summary.get('vector_crs')}")
            print(f"CRS match: {summary.get('crs_match', True)}")
            if "warning" in summary:
                print(f"Warning: {summary['warning']}")
            if "error" in summary:
                print(f"Error: {summary['error']}")
            if "bbox" in summary:
                print(f"BBox clip written to: {summary['clipped_path']}")
            print(f"Raster info keys: {', '.join(summary['raster_info_keys'])}")
            print(f"Raster resolution: {summary['raster_resolution']}")
            print(f"Vector info keys: {', '.join(summary['vector_info_keys'])}")
            print(f"Vector-to-raster output: {summary['vector_to_raster_output']}")
            print(f"Raster-to-vector output: {summary['raster_to_vector_output']}")

        return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
