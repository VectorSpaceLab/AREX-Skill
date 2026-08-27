#!/usr/bin/env python3
"""Inspect a BlenderGIS add-on/module environment without running UI operators.

Examples:
  python check_blendergis_environment.py --module BlenderGIS --json
  python check_blendergis_environment.py --addon-path /path/to/BlenderGIS

The helper is safe by default: it imports modules for read-only metadata and
reports optional dependency availability. It does not register the add-on, open
Blender UI, contact network services, or execute GIS operators.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

OPTIONAL_MODULES = ["bpy", "bmesh", "mathutils", "gpu", "PIL", "pyproj", "osgeo"]
FEATURE_FLAGS = [
    "CAM_GEOPHOTO",
    "CAM_GEOREF",
    "EXPORT_SHP",
    "GET_DEM",
    "IMPORT_GEORASTER",
    "IMPORT_OSM",
    "IMPORT_SHP",
    "IMPORT_ASC",
    "DELAUNAY",
    "TERRAIN_NODES",
    "TERRAIN_RECLASS",
    "BASEMAPS",
    "DROP",
    "EARTH_SPHERE",
]


def module_status(name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    info: Dict[str, Any] = {"available": True}
    version = getattr(module, "__version__", None)
    if version is not None:
        info["version"] = str(version)
    if name == "bpy":
        app = getattr(module, "app", None)
        if app is not None:
            info["bpy_app_version"] = list(getattr(app, "version", ()))
            info["background"] = bool(getattr(app, "background", False))
    return info


def import_addon(module_name: str, addon_path: Optional[str]) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "requested_module": module_name,
        "addon_path_supplied": bool(addon_path),
        "importable": False,
        "errors": [],
    }
    inserted_parent: Optional[str] = None
    if addon_path:
        path = Path(addon_path).resolve()
        if not path.exists():
            result["errors"].append(f"addon path does not exist: {path}")
            return result
        if not (path / "__init__.py").is_file():
            result["errors"].append(f"addon path is not a Blender add-on directory with __init__.py: {path}")
            return result
        inserted_parent = str(path.parent)
        sys.path.insert(0, inserted_parent)
        module_name = path.name
        result["requested_module"] = module_name

    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        result["errors"].append(f"{type(exc).__name__}: {exc}")
        return result
    finally:
        if inserted_parent and sys.path and sys.path[0] == inserted_parent:
            # Keep imported module alive but avoid leaking path mutation to callers that import main().
            sys.path.pop(0)

    result["importable"] = True
    bl_info = getattr(module, "bl_info", {}) or {}
    result["bl_info"] = {
        key: list(value) if isinstance(value, tuple) else value
        for key, value in bl_info.items()
        if key in {"name", "description", "version", "blender", "category", "location", "wiki_url", "tracker_url"}
    }
    result["feature_flags"] = {flag: bool(getattr(module, flag)) for flag in FEATURE_FLAGS if hasattr(module, flag)}
    result["has_register"] = callable(getattr(module, "register", None))
    result["has_unregister"] = callable(getattr(module, "unregister", None))
    menus = getattr(module, "menus", None)
    if menus is not None:
        result["menu_class_count"] = len(menus)
        result["menu_classes"] = [getattr(item, "__name__", str(item)) for item in menus]
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only BlenderGIS add-on environment diagnostic.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--module", help="Importable add-on module name, for example BlenderGIS")
    source.add_argument("--addon-path", help="Path to the BlenderGIS add-on directory containing __init__.py")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    module_name = args.module or "BlenderGIS"
    result: Dict[str, Any] = {
        "python_version": sys.version.split()[0],
        "modules": {name: module_status(name) for name in OPTIONAL_MODULES},
        "addon": import_addon(module_name, args.addon_path),
    }
    ok = bool(result["modules"].get("bpy", {}).get("available")) and bool(result["addon"].get("importable"))
    result["ok"] = ok

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Python: {result['python_version']}")
        for name, status in result["modules"].items():
            suffix = "OK" if status.get("available") else "missing"
            detail = status.get("version") or status.get("bpy_app_version") or status.get("error", "")
            print(f"{name}: {suffix} {detail}")
        addon = result["addon"]
        print(f"BlenderGIS importable: {addon.get('importable')}")
        if addon.get("bl_info"):
            print(f"bl_info: {addon['bl_info']}")
        for error in addon.get("errors", []):
            print(f"ERROR: {error}", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
