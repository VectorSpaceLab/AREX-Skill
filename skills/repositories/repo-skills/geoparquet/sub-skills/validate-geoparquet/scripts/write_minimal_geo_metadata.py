#!/usr/bin/env python3
"""Create an explicit one-row GeoParquet 2.0 metadata fixture.

Native output uses geoarrow-pyarrow so PyArrow writes a Geometry logical type.
Use --plain to deliberately write ordinary BYTE_ARRAY WKB with the same geo
metadata and exercise the non-conformant boundary.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _fixture_module():
    # Import the sibling by file location, so arbitrary CWDs are supported.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import make_wkb_fixture

    return make_wkb_fixture


def _crs84() -> dict:
    return {
        "$schema": "https://proj.org/schemas/v0.7/projjson.schema.json",
        "type": "GeographicCRS",
        "name": "WGS 84 longitude-latitude",
        "datum": {
            "type": "GeodeticReferenceFrame",
            "name": "World Geodetic System 1984",
            "ellipsoid": {
                "name": "WGS 84",
                "semi_major_axis": 6378137,
                "inverse_flattening": 298.257223563,
            },
        },
        "coordinate_system": {
            "subtype": "ellipsoidal",
            "axis": [
                {
                    "name": "Geodetic longitude",
                    "abbreviation": "Lon",
                    "direction": "east",
                    "unit": "degree",
                },
                {
                    "name": "Geodetic latitude",
                    "abbreviation": "Lat",
                    "direction": "north",
                    "unit": "degree",
                },
            ],
        },
        "id": {"authority": "OGC", "code": "CRS84"},
    }


def build_metadata(
    column: str, geometry_type: str, dimensions: str, crs_mode: str
) -> dict:
    helper = _fixture_module()
    metadata = helper._metadata(column, geometry_type, dimensions)
    if crs_mode == "null":
        metadata["columns"][column]["crs"] = None
    elif crs_mode == "crs84":
        metadata["columns"][column]["crs"] = _crs84()
    return metadata


def write(
    output: Path,
    column: str,
    geometry_type: str,
    dimensions: str,
    native: bool,
    crs_mode: str,
    force: bool = False,
) -> None:
    if output.exists() and not force:
        raise FileExistsError(f"refusing to overwrite existing output: {output} (use --force)")
    import pyarrow as pa
    import pyarrow.parquet as pq

    helper = _fixture_module()
    raw = helper.wkb_for_type(geometry_type, dimensions)
    if native:
        try:
            import geoarrow.pyarrow as ga
        except ImportError as exc:
            raise RuntimeError(
                "native output requires geoarrow-pyarrow; use --plain for a "
                "deliberate non-native fixture"
            ) from exc
        geometry = ga.as_wkb([raw])
        if crs_mode == "crs84":
            try:
                geometry = ga.with_crs(geometry, ga.OGC_CRS84)
            except Exception as exc:
                raise RuntimeError(
                    f"could not attach CRS84 to native logical type: {exc}"
                ) from exc
    else:
        geometry = pa.array([raw], type=pa.binary())

    metadata = build_metadata(column, geometry_type, dimensions, crs_mode)
    table = pa.table({column: geometry}).replace_schema_metadata(
        {"geo": json.dumps(metadata)}
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="output Parquet path")
    parser.add_argument(
        "--geometry-type",
        choices=[
            "Point",
            "LineString",
            "Polygon",
            "MultiPoint",
            "MultiLineString",
            "MultiPolygon",
            "GeometryCollection",
        ],
        default="Point",
    )
    parser.add_argument(
        "--dimensions",
        choices=["XY", "XYZ", "XYM", "XYZM"],
        default="XY",
    )
    parser.add_argument("--column", default="geometry")
    parser.add_argument(
        "--crs",
        choices=["absent", "null", "crs84"],
        default="absent",
        help="metadata CRS form; absent defaults to OGC:CRS84",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--native", action="store_true", help="write native Geometry (default)")
    mode.add_argument("--plain", action="store_true", help="write plain BYTE_ARRAY WKB")
    parser.add_argument("--force", action="store_true", help="allow replacing the output")
    args = parser.parse_args(argv)
    try:
        write(
            args.output,
            args.column,
            args.geometry_type,
            args.dimensions,
            native=not args.plain,
            crs_mode=args.crs,
            force=args.force,
        )
    except (OSError, RuntimeError, ValueError, ImportError) as exc:
        parser.error(str(exc))
    print(f"wrote {'native ' if not args.plain else 'plain '}GeoParquet fixture: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
