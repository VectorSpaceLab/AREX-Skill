#!/usr/bin/env python3
"""Validate core GeoDataFrame structure with tiny, safe checks.

Examples:
  python validate_geodataframe.py --default-fixture --build-sindex
  python validate_geodataframe.py --wkt "POINT (0 0)" "POLYGON EMPTY" --crs EPSG:4326 --json
  python validate_geodataframe.py --input-file sample.geojson --require-crs
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def build_default(crs: str):
    import geopandas as gpd
    from shapely.geometry import Point, Polygon

    return gpd.GeoDataFrame(
        {
            "label": ["point", "empty", "polygon"],
            "geometry": [Point(0, 0), Polygon(), Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
        },
        crs=crs,
    )


def build_from_wkt(wkts: list[str], crs: str):
    import geopandas as gpd

    geoms = gpd.GeoSeries.from_wkt(wkts, crs=crs)
    return gpd.GeoDataFrame({"id": list(range(len(geoms))), "geometry": geoms}, geometry="geometry", crs=crs)


def summarize(gdf: Any, geometry_column: str, build_sindex: bool) -> dict[str, Any]:
    import geopandas as gpd

    report: dict[str, Any] = {
        "is_geodataframe": isinstance(gdf, gpd.GeoDataFrame),
        "rows": int(len(gdf)),
        "columns": list(map(str, gdf.columns)),
        "active_geometry": None,
        "crs": None,
        "geometry_dtype": None,
        "missing_geometries": None,
        "empty_geometries": None,
        "invalid_geometries": None,
        "total_bounds": None,
        "sindex": "not-requested",
        "errors": [],
    }
    if not isinstance(gdf, gpd.GeoDataFrame):
        report["errors"].append("object is not a GeoDataFrame")
        return report

    if geometry_column not in gdf.columns:
        report["errors"].append(f"geometry column {geometry_column!r} not present")
        return report

    if gdf.geometry.name != geometry_column:
        try:
            gdf = gdf.set_geometry(geometry_column)
        except Exception as exc:
            report["errors"].append(f"could not set active geometry to {geometry_column!r}: {type(exc).__name__}: {exc}")
            return report

    geom = gdf.geometry
    report["active_geometry"] = geom.name
    report["crs"] = None if gdf.crs is None else gdf.crs.to_string()
    report["geometry_dtype"] = str(geom.dtype)
    report["missing_geometries"] = int(geom.isna().sum())
    report["empty_geometries"] = int(geom.is_empty.fillna(False).sum())
    report["invalid_geometries"] = int((~geom.is_valid.fillna(False)).sum())
    try:
        report["total_bounds"] = [float(x) for x in gdf.total_bounds]
    except Exception as exc:
        report["errors"].append(f"total_bounds failed: {type(exc).__name__}: {exc}")
    if build_sindex:
        try:
            sidx = gdf.sindex
            report["sindex"] = {"size": int(sidx.size), "valid_query_predicates": sorted(map(str, sidx.valid_query_predicates))}
        except Exception as exc:
            report["sindex"] = f"failed: {type(exc).__name__}: {exc}"
            report["errors"].append("spatial index build failed")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate GeoDataFrame geometry column, CRS, bounds, missing/empty geometry, and optional spatial index.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--default-fixture", action="store_true", help="Use a built-in tiny point/empty/polygon fixture.")
    source.add_argument("--input-file", type=Path, help="Read a file with geopandas.read_file for validation.")
    source.add_argument("--wkt", nargs="+", help="Build a GeoDataFrame from one or more WKT strings.")
    parser.add_argument("--geometry-column", default="geometry", help="Geometry column to require or activate.")
    parser.add_argument("--crs", default="EPSG:4326", help="CRS for default or WKT fixtures.")
    parser.add_argument("--require-crs", action="store_true", help="Fail when the GeoDataFrame has no CRS metadata.")
    parser.add_argument("--build-sindex", action="store_true", help="Also build and summarize the spatial index.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    args = parser.parse_args(argv)

    try:
        import geopandas as gpd
    except Exception as exc:
        print(f"failed to import geopandas: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    try:
        if args.input_file:
            gdf = gpd.read_file(args.input_file)
        elif args.wkt:
            gdf = build_from_wkt(args.wkt, args.crs)
        else:
            gdf = build_default(args.crs)
        report = summarize(gdf, args.geometry_column, args.build_sindex)
    except Exception as exc:
        report = {"errors": [f"validation failed: {type(exc).__name__}: {exc}"]}

    if args.require_crs and not report.get("crs"):
        report.setdefault("errors", []).append("CRS is required but missing")

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("GeoDataFrame validation report")
        for key, value in report.items():
            print(f"{key}: {value}")

    return 0 if not report.get("errors") else 1


if __name__ == "__main__":
    raise SystemExit(main())
