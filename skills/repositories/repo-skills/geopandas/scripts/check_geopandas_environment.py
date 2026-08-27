#!/usr/bin/env python3
"""Check a Python environment for GeoPandas package workflows.

This helper is intentionally small and safe: it imports GeoPandas, reports base
and optional dependencies, and runs tiny in-memory GeoDataFrame/spatial-join
checks. It does not read the source repository, download data, call network
services, or write outside temporary directories.

Examples:
  python check_geopandas_environment.py
  python check_geopandas_environment.py --json --require-optional pyarrow folium
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib.metadata import PackageNotFoundError, version


def _dist_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def _import_status(name: str) -> dict[str, object]:
    try:
        module = importlib.import_module(name)
        return {"available": True, "module": name, "version": getattr(module, "__version__", _dist_version(name))}
    except Exception as exc:  # optional dependency diagnostics should not traceback first
        return {"available": False, "module": name, "error": f"{type(exc).__name__}: {exc}"}


def run_smoke() -> dict[str, object]:
    import geopandas as gpd
    from shapely.geometry import Point, Polygon

    gdf = gpd.GeoDataFrame(
        {"name": ["a", "b"], "geometry": [Point(0, 0), Point(1, 1)]},
        crs="EPSG:4326",
    )
    projected = gdf.to_crs(3857)
    if projected.crs.to_epsg() != 3857:
        raise AssertionError("to_crs(3857) did not set EPSG:3857")

    left = gpd.GeoDataFrame({"id": [1], "geometry": [Point(0.5, 0.5)]}, crs="EPSG:4326")
    right = gpd.GeoDataFrame(
        {"zone": ["unit"], "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]},
        crs="EPSG:4326",
    )
    joined = gpd.sjoin(left, right, predicate="within", how="inner")
    if joined["zone"].tolist() != ["unit"]:
        raise AssertionError("spatial join smoke returned unexpected rows")

    return {
        "geodataframe_rows": len(gdf),
        "crs": gdf.crs.to_string(),
        "projected_crs": projected.crs.to_string(),
        "sjoin_rows": len(joined),
        "sjoin_columns": list(joined.columns),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check GeoPandas imports, versions, optional dependencies, and tiny API smoke behavior.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of a text report.")
    parser.add_argument(
        "--require-optional",
        nargs="*",
        default=[],
        metavar="MODULE",
        help="Optional import module names that must be available for a zero exit status.",
    )
    args = parser.parse_args(argv)

    base_modules = ["geopandas", "pandas", "numpy", "shapely", "pyproj", "pyogrio"]
    optional_modules = ["fiona", "pyarrow", "sqlalchemy", "psycopg", "geopy", "matplotlib", "folium", "mapclassify", "contextily", "xyzservices", "pointpats", "scipy"]
    report: dict[str, object] = {
        "python": sys.version.split()[0],
        "base": {name: _import_status(name) for name in base_modules},
        "optional": {name: _import_status(name) for name in optional_modules},
        "smoke": None,
        "errors": [],
    }

    try:
        report["smoke"] = run_smoke()
    except Exception as exc:
        report["errors"].append(f"smoke failed: {type(exc).__name__}: {exc}")

    missing_required = [name for name in args.require_optional if not report["optional"].get(name, _import_status(name)).get("available")]
    if missing_required:
        report["errors"].append("missing required optional modules: " + ", ".join(missing_required))

    ok = not report["errors"] and all(item.get("available") for item in report["base"].values())
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("GeoPandas environment check")
        print(f"Python: {report['python']}")
        for section in ["base", "optional"]:
            print(f"\n{section.title()} modules:")
            for name, status in report[section].items():
                if status.get("available"):
                    print(f"  OK      {name} {status.get('version') or ''}".rstrip())
                else:
                    print(f"  MISSING {name}: {status.get('error')}")
        print(f"\nSmoke: {report['smoke']}")
        if report["errors"]:
            print("\nErrors:")
            for err in report["errors"]:
                print(f"  - {err}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
