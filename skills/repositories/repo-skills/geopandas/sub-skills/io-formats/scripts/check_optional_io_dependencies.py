#!/usr/bin/env python3
"""Report optional dependencies relevant to GeoPandas I/O and adjacent workflows.

Examples:
  python check_optional_io_dependencies.py
  python check_optional_io_dependencies.py --json --require pyarrow sqlalchemy psycopg
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib.metadata import PackageNotFoundError, version

MODULES = {
    "fiona": "optional Fiona vector file engine",
    "pyarrow": "Parquet, Feather, Arrow, and GeoArrow workflows",
    "sqlalchemy": "SQL/PostGIS connection management",
    "psycopg": "PostgreSQL/PostGIS driver",
    "geoalchemy2": "PostGIS SQLAlchemy geometry typing",
    "geopy": "geocoding providers",
    "matplotlib": "static plotting",
    "folium": "interactive explore maps",
    "mapclassify": "choropleth classification",
    "branca": "folium color maps",
    "contextily": "web basemap tiles",
    "xyzservices": "tile provider catalog",
}


def status(name: str) -> dict[str, object]:
    try:
        mod = importlib.import_module(name)
        try:
            dist_version = version(name)
        except PackageNotFoundError:
            dist_version = getattr(mod, "__version__", None)
        return {"available": True, "version": dist_version, "purpose": MODULES[name]}
    except Exception as exc:
        return {"available": False, "error": f"{type(exc).__name__}: {exc}", "purpose": MODULES[name]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check optional GeoPandas dependency modules without importing private repo state.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    parser.add_argument("--require", nargs="*", default=[], metavar="MODULE", help="Module names that must be importable for success.")
    args = parser.parse_args(argv)

    unknown = sorted(set(args.require) - set(MODULES))
    if unknown:
        print("unknown optional module(s): " + ", ".join(unknown), file=sys.stderr)
        return 2

    report = {name: status(name) for name in MODULES}
    missing_required = [name for name in args.require if not report[name]["available"]]

    if args.json:
        print(json.dumps({"modules": report, "missing_required": missing_required}, indent=2, sort_keys=True))
    else:
        print("GeoPandas optional dependency report")
        for name, item in report.items():
            if item["available"]:
                print(f"OK      {name:12s} {item.get('version') or ''} - {item['purpose']}".rstrip())
            else:
                print(f"MISSING {name:12s} - {item['purpose']} ({item['error']})")
        if missing_required:
            print("\nMissing required optional modules: " + ", ".join(missing_required))
    return 0 if not missing_required else 1


if __name__ == "__main__":
    raise SystemExit(main())
