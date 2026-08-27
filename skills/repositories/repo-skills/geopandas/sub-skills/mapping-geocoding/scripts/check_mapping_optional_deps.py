#!/usr/bin/env python3
"""Check optional GeoPandas mapping and geocoding dependencies.

Examples:
  python check_mapping_optional_deps.py
  python check_mapping_optional_deps.py --json --require matplotlib folium geopy
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib.metadata import PackageNotFoundError, version

MODULES = {
    "matplotlib": "static GeoPandas .plot output",
    "mapclassify": "classification schemes for choropleths",
    "folium": "interactive Leaflet maps from .explore",
    "branca": "folium colormap support",
    "xyzservices": "tile provider catalog",
    "contextily": "basemap tile helpers for selected workflows",
    "geopy": "geocode and reverse_geocode providers",
}


def check(name: str) -> dict[str, object]:
    try:
        mod = importlib.import_module(name)
        try:
            v = version(name)
        except PackageNotFoundError:
            v = getattr(mod, "__version__", None)
        return {"available": True, "version": v, "purpose": MODULES[name]}
    except Exception as exc:
        return {"available": False, "error": f"{type(exc).__name__}: {exc}", "purpose": MODULES[name]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report optional dependencies for GeoPandas mapping and geocoding workflows.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    parser.add_argument("--require", nargs="*", default=[], metavar="MODULE", help="Optional modules that must be available.")
    args = parser.parse_args(argv)

    unknown = sorted(set(args.require) - set(MODULES))
    if unknown:
        print("unknown module(s): " + ", ".join(unknown), file=sys.stderr)
        return 2

    report = {name: check(name) for name in MODULES}
    missing = [name for name in args.require if not report[name]["available"]]

    if args.json:
        print(json.dumps({"modules": report, "missing_required": missing}, indent=2, sort_keys=True))
    else:
        print("GeoPandas mapping/geocoding optional dependency report")
        for name, item in report.items():
            if item["available"]:
                print(f"OK      {name:12s} {item.get('version') or ''} - {item['purpose']}".rstrip())
            else:
                print(f"MISSING {name:12s} - {item['purpose']} ({item['error']})")
        if missing:
            print("\nMissing required optional modules: " + ", ".join(missing))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
