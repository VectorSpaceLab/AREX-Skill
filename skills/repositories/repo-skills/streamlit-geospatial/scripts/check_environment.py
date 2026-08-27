#!/usr/bin/env python3
"""Run a safe, offline import/version preflight for the app dependencies.

The checker sets USE_FOLIUM before importing geemap.foliumap, prints only
package names and versions, and never starts Streamlit, authenticates Earth
Engine, contacts remote services, or prints module paths.
"""
from __future__ import annotations

import importlib
import importlib.metadata as metadata
import os
import sys

os.environ.setdefault("USE_FOLIUM", "1")

DISTRIBUTIONS = {
    "streamlit": "streamlit",
    "leafmap": "leafmap",
    "geemap": "geemap",
    "geopandas": "geopandas",
    "fiona": "fiona",
    "folium": "folium",
    "pydeck": "pydeck",
    "earthengine-api": "ee",
    "rasterio": "rasterio",
    "localtileserver": "localtileserver",
    "keplergl": "keplergl",
}


def main() -> int:
    failures: list[str] = []
    print(f"python={sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print("USE_FOLIUM=1")
    for distribution, module_name in DISTRIBUTIONS.items():
        try:
            version = metadata.version(distribution)
        except metadata.PackageNotFoundError:
            version = "not-installed"
            failures.append(f"distribution:{distribution}")
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - report optional import clearly.
            failures.append(f"import:{module_name} ({type(exc).__name__}: {exc})")
            print(f"{distribution}={version} import=failed")
        else:
            print(f"{distribution}={version} import=ok")
    if failures:
        print("failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("status=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
