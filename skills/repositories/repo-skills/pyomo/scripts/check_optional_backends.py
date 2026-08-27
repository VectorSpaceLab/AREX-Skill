#!/usr/bin/env python3
"""Check importability of optional Pyomo backends and dependencies.

This helper is safe to run from any working directory. It reports whether the
most common optional Pyomo dependencies and extension modules can be imported in
the active environment.
"""

from __future__ import annotations

import argparse
import json
from importlib import metadata

DEFAULT_MODULES = [
    "numpy",
    "scipy",
    "networkx",
    "matplotlib",
    "pandas",
    "pint",
    "pympler",
    "pyutilib",
    "qtconsole",
    "PySide6",
    "PyQt6",
    "PyQt5",
    "community",
    "casadi",
    "pyomo.contrib.appsi",
    "pyomo.contrib.fbbt.fbbt",
    "pyomo.contrib.simplification.simplify",
    "pyomo.contrib.community_detection.detection",
    "pyomo.contrib.pynumero",
    "pyomo.contrib.viewer.pyomo_viewer",
]


def probe(name: str) -> dict[str, object]:
    try:
        module = __import__(name, fromlist=["*"])
        top_level = name.split(".", 1)[0]
        try:
            version = metadata.version(top_level)
        except Exception:
            version = None
        return {
            "module": name,
            "status": "ok",
            "version": version,
            "location": getattr(module, "__file__", None),
            "error": None,
        }
    except Exception as exc:  # pragma: no cover - surfaced in manual runs
        return {
            "module": name,
            "status": "missing",
            "version": None,
            "location": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--module",
        action="append",
        dest="modules",
        default=None,
        help="Optional module or package name to probe. May be repeated.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of plain text.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return a nonzero exit code when any probe is missing.",
    )
    args = parser.parse_args()

    modules = args.modules or DEFAULT_MODULES
    results = [probe(name) for name in modules]
    missing = [item for item in results if item["status"] != "ok"]

    if args.json:
        print(json.dumps({"results": results}, indent=2, sort_keys=True))
    else:
        for item in results:
            if item["status"] == "ok":
                print(f"OK {item['module']}{' ' + str(item['version']) if item['version'] else ''}")
            else:
                print(f"MISS {item['module']}: {item['error']}")
        print(f"summary ok={len(results) - len(missing)} missing={len(missing)}")
    return 0 if (not missing or not args.strict) else 1


if __name__ == "__main__":
    raise SystemExit(main())
