#!/usr/bin/env python3
"""Write a deterministic one-row WKB GeoParquet fixture without network access."""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
from typing import Iterable

BASE_CODES = {
    "Point": 1,
    "LineString": 2,
    "Polygon": 3,
    "MultiPoint": 4,
    "MultiLineString": 5,
    "MultiPolygon": 6,
    "GeometryCollection": 7,
}
DIMENSIONS = {"XY": 0, "XYZ": 1000, "XYM": 2000, "XYZM": 3000}
_COORD_COUNTS = {"XY": 2, "XYZ": 3, "XYM": 3, "XYZM": 4}


def _coords(values: Iterable[float], dimension: str) -> bytes:
    values = tuple(values)
    count = _COORD_COUNTS[dimension]
    return struct.pack("<" + "d" * count, *values[:count])


def _header(base: str, dimension: str) -> bytes:
    return struct.pack("<BI", 1, BASE_CODES[base] + DIMENSIONS[dimension])


def _point(x: float, y: float, dimension: str) -> bytes:
    values = (x, y, 10.0, 20.0) if dimension == "XYZM" else (x, y, 10.0)
    return _header("Point", dimension) + _coords(values, dimension)


def _linestring(points: list[tuple[float, float]], dimension: str) -> bytes:
    body = struct.pack("<I", len(points))
    body += b"".join(
        _coords((x, y, 10.0, 20.0), dimension) for x, y in points
    )
    return _header("LineString", dimension) + body


def _polygon(dimension: str) -> bytes:
    ring = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)]
    body = struct.pack("<II", 1, len(ring))
    body += b"".join(
        _coords((x, y, 10.0, 20.0), dimension) for x, y in ring
    )
    return _header("Polygon", dimension) + body


def wkb_for_type(geometry_type: str, dimension: str = "XY") -> bytes:
    """Return one valid little-endian ISO WKB geometry."""
    if geometry_type == "Point":
        return _point(0.0, 0.0, dimension)
    if geometry_type == "LineString":
        return _linestring([(0.0, 0.0), (1.0, 1.0)], dimension)
    if geometry_type == "Polygon":
        return _polygon(dimension)
    if geometry_type == "MultiPoint":
        children = [_point(0.0, 0.0, dimension), _point(1.0, 1.0, dimension)]
    elif geometry_type == "MultiLineString":
        children = [_linestring([(0.0, 0.0), (1.0, 1.0)], dimension)]
    elif geometry_type == "MultiPolygon":
        children = [_polygon(dimension)]
    elif geometry_type == "GeometryCollection":
        children = [
            _point(0.0, 0.0, dimension),
            _linestring([(0.0, 0.0), (1.0, 1.0)], dimension),
        ]
    else:
        raise ValueError(f"unsupported geometry type: {geometry_type}")
    return _header(geometry_type, dimension) + struct.pack("<I", len(children)) + b"".join(children)


def _metadata(column: str, geometry_type: str, dimension: str) -> dict:
    suffix = {"XY": "", "XYZ": " Z", "XYM": " M", "XYZM": " ZM"}[dimension]
    if dimension in ("XY", "XYM"):
        bbox = [0.0, 0.0, 1.0, 1.0]
    elif dimension == "XYZ":
        bbox = [0.0, 0.0, 10.0, 1.0, 1.0, 10.0]
    else:
        bbox = [0.0, 0.0, 10.0, 20.0, 1.0, 1.0, 10.0, 20.0]
    return {
        "version": "2.0.0",
        "primary_column": column,
        "columns": {
            column: {
                "encoding": "WKB",
                "geometry_types": [geometry_type + suffix],
                "bbox": bbox,
            }
        },
    }


def write_fixture(
    output: Path,
    geometry_type: str,
    dimension: str,
    column: str,
    native: bool,
    force: bool = False,
) -> None:
    if output.exists() and not force:
        raise FileExistsError(f"refusing to overwrite existing output: {output} (use --force)")
    import pyarrow as pa
    import pyarrow.parquet as pq

    raw = wkb_for_type(geometry_type, dimension)
    if native:
        try:
            import geoarrow.pyarrow as ga
        except ImportError as exc:
            raise RuntimeError(
                "native fixture requires geoarrow-pyarrow; use --plain for "
                "a deliberate non-native fixture"
            ) from exc
        geometry = ga.as_wkb([raw])
    else:
        geometry = pa.array([raw], type=pa.binary())
    table = pa.table({column: geometry}).replace_schema_metadata(
        {"geo": json.dumps(_metadata(column, geometry_type, dimension))}
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="output Parquet path")
    parser.add_argument(
        "--geometry-type",
        choices=sorted(BASE_CODES),
        default="Point",
        help="one supported WKB base type",
    )
    parser.add_argument(
        "--dimensions",
        choices=sorted(DIMENSIONS),
        default="XY",
        help="coordinate layout: XY, XYZ, XYM, or XYZM",
    )
    parser.add_argument("--column", default="geometry", help="root geometry column name")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--native", action="store_true", help="write native Geometry (default)")
    mode.add_argument("--plain", action="store_true", help="write plain BYTE_ARRAY WKB")
    parser.add_argument("--force", action="store_true", help="allow replacing the output")
    args = parser.parse_args(argv)
    try:
        write_fixture(
            args.output,
            args.geometry_type,
            args.dimensions,
            args.column,
            native=not args.plain,
            force=args.force,
        )
    except (OSError, RuntimeError, ValueError, ImportError) as exc:
        parser.error(str(exc))
    kind = "native " if not args.plain else "plain "
    print(f"wrote {kind}WKB fixture: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
