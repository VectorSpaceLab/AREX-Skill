#!/usr/bin/env python3
"""Demonstrate GeoPandas assertion helpers on tiny fixtures.

Examples:
  python geopandas_assertion_demo.py
  python geopandas_assertion_demo.py --json
"""

from __future__ import annotations

import argparse
import json


def run_demo() -> dict[str, object]:
    import geopandas as gpd
    from geopandas.testing import assert_geodataframe_equal, assert_geoseries_equal
    from shapely.geometry import Point

    expected = gpd.GeoDataFrame(
        {"name": ["a", "b"], "geometry": [Point(0, 0), Point(1, 1)]},
        crs="EPSG:4326",
    )
    actual = expected.copy()
    assert_geodataframe_equal(actual, expected)
    assert_geoseries_equal(actual.geometry, expected.geometry)

    reordered = actual.sort_values("name", ascending=False).sort_values("name").reset_index(drop=True)
    expected_reset = expected.reset_index(drop=True)
    assert_geodataframe_equal(reordered, expected_reset)

    mismatch = expected.copy()
    mismatch = mismatch.set_crs("EPSG:3857", allow_override=True)
    caught = None
    try:
        assert_geodataframe_equal(mismatch, expected)
    except AssertionError as exc:
        lines = str(exc).splitlines()
        caught = lines[0] if lines else repr(exc)
    if not caught:
        raise AssertionError("CRS mismatch was not caught by assert_geodataframe_equal")

    return {
        "equal_frame_assertion": "passed",
        "equal_series_assertion": "passed",
        "sorted_reset_assertion": "passed",
        "intentional_crs_mismatch_caught": caught,
        "rows": len(expected),
        "crs": expected.crs.to_string(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run tiny GeoPandas testing assertion examples.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    args = parser.parse_args(argv)

    report = {"errors": [], "result": None}
    try:
        report["result"] = run_demo()
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("GeoPandas assertion helper demo")
        print(report)
    return 0 if not report["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
