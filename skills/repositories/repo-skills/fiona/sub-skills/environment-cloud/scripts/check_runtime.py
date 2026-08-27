#!/usr/bin/env python3
"""Safely report generic Fiona/GDAL runtime facts.

No paths, credentials, environment-variable values, downloads, or data writes
are printed or performed. Run with the Fiona installation selected by the user.
"""

from __future__ import annotations

import argparse
import importlib.util


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Fiona/GDAL runtime facts safely")
    parser.parse_args()
    try:
        import fiona
    except Exception as exc:  # pragma: no cover - diagnostic failure path
        print(f"fiona import: FAILED ({type(exc).__name__}: {exc})")
        return 1

    print(f"fiona version: {getattr(fiona, '__version__', 'unknown')}")
    print(f"gdal release: {getattr(fiona, '__gdal_version__', 'unknown')}")
    drivers = getattr(fiona, "supported_drivers", {})
    print(f"supported drivers: {len(drivers)}")
    print("driver names: " + ", ".join(sorted(drivers)))
    for name in ("boto3", "shapely", "fsspec"):
        print(f"optional {name}: {'available' if importlib.util.find_spec(name) else 'missing'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
