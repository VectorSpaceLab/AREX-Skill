#!/usr/bin/env python3
"""Run tiny deterministic GeoPandas spatial operation checks.

Examples:
  python spatial_operations_smoke.py
  python spatial_operations_smoke.py --json
"""

from __future__ import annotations

import argparse
import json
import sys


def run_checks() -> dict[str, object]:
    import geopandas as gpd
    from shapely.geometry import Point, Polygon, box

    points = gpd.GeoDataFrame(
        {"id": [1, 2], "group": ["a", "a"], "geometry": [Point(0.25, 0.25), Point(1.25, 0.25)]},
        crs="EPSG:4326",
    )
    polygons = gpd.GeoDataFrame(
        {"zone": ["left", "right"], "geometry": [box(0, 0, 1, 1), box(1, 0, 2, 1)]},
        crs="EPSG:4326",
    )

    joined = gpd.sjoin(points, polygons, predicate="within", how="left")
    if joined["zone"].tolist() != ["left", "right"]:
        raise AssertionError(f"unexpected sjoin zones: {joined['zone'].tolist()}")

    overlap_a = gpd.GeoDataFrame({"a": [1], "geometry": [box(0, 0, 1.5, 1)]}, crs="EPSG:4326")
    overlap_b = gpd.GeoDataFrame({"b": [2], "geometry": [box(1, 0, 2, 1)]}, crs="EPSG:4326")
    over = gpd.overlay(overlap_a, overlap_b, how="intersection")
    overlay_area = float(over.geometry.iloc[0].area)
    if len(over) != 1 or round(overlay_area, 6) != 0.5:
        raise AssertionError("overlay intersection area was not 0.5 in source units")

    clipped = gpd.clip(polygons, gpd.GeoDataFrame({"geometry": [box(0.5, -0.5, 1.5, 0.5)]}, crs="EPSG:4326"))
    if len(clipped) != 2:
        raise AssertionError("clip should touch both polygons")

    dissolved = polygons.dissolve(by=None)
    if len(dissolved) != 1:
        raise AssertionError("dissolve by None should produce one row")

    sidx = polygons.sindex
    query = sidx.query(Point(0.25, 0.25), predicate="intersects")
    if len(query) != 1:
        raise AssertionError("spatial index query should find one polygon")

    return {
        "sjoin_rows": int(len(joined)),
        "sjoin_zones": joined["zone"].tolist(),
        "overlay_area_source_units": overlay_area,
        "clip_rows": int(len(clipped)),
        "dissolve_rows": int(len(dissolved)),
        "sindex_size": int(sidx.size),
        "valid_query_predicates": sorted(map(str, sidx.valid_query_predicates)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run tiny GeoPandas spatial operation assertions.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    args = parser.parse_args(argv)

    report = {"errors": [], "checks": None}
    try:
        report["checks"] = run_checks()
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("GeoPandas spatial operations smoke")
        print(report)
    return 0 if not report["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
