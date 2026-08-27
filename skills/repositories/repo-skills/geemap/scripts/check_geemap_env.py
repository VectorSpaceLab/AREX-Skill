#!/usr/bin/env python3
"""Safe geemap environment smoke check.

This helper verifies package import, version, selected modules, optional extras,
and optional Earth Engine authentication state without running exports, downloads,
or network-heavy workflows by default.

Examples:
  python check_geemap_env.py --skip-ee-auth
  python check_geemap_env.py --backend folium --skip-ee-auth
  python check_geemap_env.py --check-ee-auth
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from importlib import metadata


def try_import(name: str) -> dict:
    try:
        module = importlib.import_module(name)
        return {"name": name, "ok": True, "module": getattr(module, "__name__", name)}
    except Exception as exc:  # noqa: BLE001 - diagnostic helper
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def check_backend(backend: str, skip_ee_init: bool) -> dict:
    env_before = os.environ.get("USE_FOLIUM")
    if backend == "folium":
        os.environ["USE_FOLIUM"] = "1"
    elif backend == "ipyleaflet" and "USE_FOLIUM" in os.environ:
        # Report what the user requested without permanently changing the parent shell.
        os.environ.pop("USE_FOLIUM", None)

    result = {"backend": backend, "ok": False, "methods": {}, "error": None}
    try:
        if backend == "folium":
            # Top-level `import geemap` may set `geemap.basemaps` to a registry
            # object. Restore the helper module before importing foliumap so a
            # same-process `--backend both` diagnostic can still exercise folium.
            pkg = importlib.import_module("geemap")
            basemap_module = importlib.import_module("geemap.basemaps")
            setattr(pkg, "basemaps", basemap_module)
            module = importlib.import_module("geemap.foliumap")
            Map = module.Map
            map_obj = Map(ee_initialize=not skip_ee_init)
        else:
            module = importlib.import_module("geemap")
            Map = module.Map
            map_obj = Map(ee_initialize=not skip_ee_init)
        result["map_class"] = f"{Map.__module__}.{Map.__name__}"
        for method in [
            "add_layer",
            "addLayer",
            "add_ee_layer",
            "set_center",
            "center_object",
            "add_basemap",
            "add_tile_layer",
            "add_wms_layer",
            "split_map",
            "add_legend",
            "add_colorbar",
            "to_html",
            "to_streamlit",
        ]:
            result["methods"][method] = hasattr(map_obj, method)
        result["ok"] = True
    except Exception as exc:  # noqa: BLE001 - diagnostic helper
        result["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        if env_before is None:
            os.environ.pop("USE_FOLIUM", None)
        else:
            os.environ["USE_FOLIUM"] = env_before
    return result


def check_ee_auth() -> dict:
    try:
        ee = importlib.import_module("ee")
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "stage": "import", "error": f"{type(exc).__name__}: {exc}"}
    try:
        ee.Initialize()
        # Tiny metadata-free object construction; do not call getInfo().
        _ = ee.Geometry.Point([0, 0])
        return {"ok": True, "stage": "initialize"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "stage": "initialize", "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check geemap import, optional modules, backend map construction, and optional Earth Engine auth.")
    parser.add_argument("--backend", choices=["ipyleaflet", "folium", "both"], default="ipyleaflet", help="Map backend to construct with ee_initialize disabled by default.")
    parser.add_argument("--check-ee-auth", action="store_true", help="Attempt ee.Initialize(); may require credentials/network/project.")
    parser.add_argument("--skip-ee-auth", action="store_true", help="Do not attempt Earth Engine initialization. This is the safe default.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    args = parser.parse_args()

    skip_ee_init = True
    checks = {
        "python": sys.version.split()[0],
        "distributions": {name: dist_version(name) for name in ["geemap", "earthengine-api", "ipyleaflet", "folium"]},
        "imports": [try_import(name) for name in ["geemap", "geemap.common", "geemap.conversion", "geemap.ml", "geemap.chart", "geemap.timelapse"]],
        "optional_imports": [try_import(name) for name in ["cartopy", "pydeck", "keplergl", "geopandas", "maplibre", "localtileserver", "osmnx", "google.generativeai"]],
        "backends": [],
        "earth_engine": {"checked": False, "ok": None},
    }

    backends = ["ipyleaflet", "folium"] if args.backend == "both" else [args.backend]
    for backend in backends:
        checks["backends"].append(check_backend(backend, skip_ee_init=skip_ee_init))

    if args.check_ee_auth and not args.skip_ee_auth:
        checks["earth_engine"] = {"checked": True, **check_ee_auth()}

    required_ok = all(item["ok"] for item in checks["imports"][:1]) and all(item["ok"] for item in checks["backends"])

    if args.json:
        print(json.dumps(checks, indent=2, sort_keys=True))
    else:
        print(f"Python: {checks['python']}")
        print("Distributions:")
        for name, version in checks["distributions"].items():
            print(f"  {name}: {version or 'not installed'}")
        print("Imports:")
        for item in checks["imports"]:
            print(f"  {item['name']}: {'OK' if item['ok'] else item['error']}")
        print("Optional imports:")
        for item in checks["optional_imports"]:
            print(f"  {item['name']}: {'OK' if item['ok'] else item['error']}")
        print("Backends:")
        for item in checks["backends"]:
            print(f"  {item['backend']}: {'OK' if item['ok'] else item['error']}")
            if item.get("methods"):
                available = ", ".join(name for name, ok in item["methods"].items() if ok)
                print(f"    methods: {available}")
        if checks["earth_engine"]["checked"]:
            print(f"Earth Engine: {'OK' if checks['earth_engine']['ok'] else checks['earth_engine'].get('error')}")
        else:
            print("Earth Engine: not checked (safe default)")

    return 0 if required_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
