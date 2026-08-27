#!/usr/bin/env python3
"""Offline-first geemap interactive-map smoke check.

The script imports a requested geemap map backend, optionally skips Earth
Engine initialization, constructs a minimal Map, and prints method/module
availability for the interactive-map APIs covered by this skill.

No network or Earth Engine authentication is required by default, and no source
repository checkout is required. It expects geemap to be importable from the
active Python environment.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import os
import sys
from types import ModuleType
from typing import Any

BACKEND_MODULES = {
    "ipyleaflet": "geemap.geemap",
    "folium": "geemap.foliumap",
}

METHODS = [
    "add_layer",
    "addLayer",
    "add_ee_layer",
    "set_center",
    "setCenter",
    "center_object",
    "centerObject",
    "add_basemap",
    "add_tile_layer",
    "add_wms_layer",
    "split_map",
    "add_legend",
    "add_colorbar",
    "add_raster",
    "add_cog_layer",
    "add_stac_layer",
    "to_html",
    "to_streamlit",
    "add_draw_control",
    "add_layer_manager",
    "add_inspector",
]

HELPER_MODULES = [
    "geemap.core",
    "geemap.ee_tile_layers",
    "geemap.basemaps",
    "geemap.map_widgets",
    "geemap.toolbar",
]

EXPECTED_HELPERS = {
    "geemap.ee_tile_layers": ["EELeafletTileLayer", "EEFoliumTileLayer"],
    "geemap.basemaps": ["get_xyz_dict", "xyz_to_leaflet", "xyz_to_folium", "search_qms"],
    "geemap.map_widgets": ["Inspector", "LayerManager", "Legend", "Colorbar"],
    "geemap.toolbar": ["Toolbar", "get_main_tools", "get_extra_tools"],
}

COMMON_REQUIRED = {
    "geemap",
    "eerepr",
    "ee",
    "earthengine-api",
    "ipyleaflet",
    "folium",
    "anywidget",
    "ipywidgets",
    "box",
    "xyzservices",
}


def _status(value: bool) -> str:
    return "ok" if value else "missing"


def _yesno(value: bool) -> str:
    return "yes" if value else "no"


def _safe_signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception:
        return ""


def _print_import_error(exc: BaseException) -> None:
    print(f"import_backend: failed ({exc.__class__.__name__}: {exc})")
    missing = getattr(exc, "name", None)
    if missing:
        print(f"missing_module: {missing}")
        if missing in COMMON_REQUIRED or missing.split(".")[0] in COMMON_REQUIRED:
            print(
                "hint: install or repair geemap base dependencies in the active "
                "Python environment, then restart the notebook kernel/runtime."
            )
    else:
        print("hint: inspect the traceback in the active environment if import keeps failing.")


def _import_module(name: str) -> tuple[ModuleType | None, BaseException | None]:
    try:
        return importlib.import_module(name), None
    except BaseException as exc:  # noqa: BLE001 - diagnostic script should report all import failures.
        return None, exc


def _print_helper_modules() -> bool:
    all_ok = True
    print("\nhelper_modules:")
    for module_name in HELPER_MODULES:
        module, exc = _import_module(module_name)
        if module is None:
            all_ok = False
            print(f"  {module_name}: failed ({exc.__class__.__name__}: {exc})")
            continue
        print(f"  {module_name}: ok")
        for helper in EXPECTED_HELPERS.get(module_name, []):
            print(f"    {helper}: {_status(hasattr(module, helper))}")
    return all_ok


def _print_basemap_shadowing(module: ModuleType) -> None:
    registry = getattr(module, "basemaps", None)
    print("\nbasemap_registry:")
    print(f"  backend_module_has_basemaps: {_status(registry is not None)}")
    if registry is None:
        return
    print(f"  backend_module_basemaps_type: {type(registry).__module__}.{type(registry).__name__}")
    print(f"  backend_module_basemaps_has_keys: {_status(hasattr(registry, 'keys'))}")
    print(f"  backend_module_basemaps_has_get_xyz_dict: {_status(hasattr(registry, 'get_xyz_dict'))}")
    try:
        size = len(registry)  # type: ignore[arg-type]
    except Exception:
        size = "unknown"
    print(f"  backend_module_basemaps_size: {size}")


def _print_methods(map_cls: type[Any]) -> bool:
    all_required = True
    print("\nmethod_availability:")
    for name in METHODS:
        attr = getattr(map_cls, name, None)
        available = attr is not None
        if not available:
            # Some methods are intentionally backend-specific. Keep the report factual.
            all_required = False
            print(f"  {name}: missing")
            continue
        sig = _safe_signature(attr)
        suffix = f" {sig}" if sig else ""
        print(f"  {name}: ok{suffix}")
    return all_required


def _instantiate_map(map_cls: type[Any], skip_ee_init: bool) -> bool:
    init_kwargs: dict[str, Any] = {}
    if skip_ee_init:
        init_kwargs["ee_initialize"] = False
    print("\nmap_instance:")
    print(f"  ee_initialize_skipped: {_yesno(skip_ee_init)}")
    try:
        map_obj = map_cls(**init_kwargs)
    except BaseException as exc:  # noqa: BLE001 - diagnostic script should not hide import/init failures.
        print(f"  status: failed ({exc.__class__.__name__}: {exc})")
        print("  hint: retry with --skip-ee-init, then check install/widget dependencies.")
        return False

    print("  status: ok")
    print(f"  instance_class: {map_obj.__class__.__module__}.{map_obj.__class__.__name__}")
    print(f"  baseclass_attr: {getattr(map_obj, 'baseclass', 'n/a')}")
    if hasattr(map_obj, "controls"):
        try:
            print(f"  controls_count: {len(map_obj.controls)}")
        except Exception:
            print("  controls_count: unknown")
    if hasattr(map_obj, "layers"):
        try:
            print(f"  layers_count: {len(map_obj.layers)}")
        except Exception:
            print("  layers_count: unknown")
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Offline geemap backend smoke check: imports a selected backend, "
            "constructs Map with Earth Engine initialization skipped by default, "
            "and prints method/module availability."
        )
    )
    parser.add_argument(
        "--backend",
        choices=sorted(BACKEND_MODULES),
        default="ipyleaflet",
        help="Map backend to inspect. Default: ipyleaflet.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--skip-ee-init",
        dest="skip_ee_init",
        action="store_true",
        help="Skip Earth Engine initialization. This is the safe default.",
    )
    group.add_argument(
        "--init-ee",
        dest="skip_ee_init",
        action="store_false",
        help="Attempt Earth Engine initialization during Map construction.",
    )
    parser.set_defaults(skip_ee_init=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    module_name = BACKEND_MODULES[args.backend]
    if args.backend == "folium":
        # geemap chooses its top-level backend during package import. Set this
        # before importing geemap.foliumap so the diagnostic works even when the
        # caller has not exported USE_FOLIUM in the shell.
        os.environ.setdefault("USE_FOLIUM", "1")
    print("geemap_interactive_map_smoke")
    print(f"backend_requested: {args.backend}")
    print(f"backend_module: {module_name}")
    print(f"USE_FOLIUM_env_set: {_yesno(os.environ.get('USE_FOLIUM') is not None)}")

    module, exc = _import_module(module_name)
    if module is None:
        _print_import_error(exc if exc is not None else RuntimeError("unknown import failure"))
        return 2

    print("import_backend: ok")
    version = getattr(importlib.import_module("geemap"), "__version__", "unknown")
    print(f"geemap_version: {version}")

    map_cls = getattr(module, "Map", None)
    print(f"Map_class_available: {_status(map_cls is not None)}")
    if map_cls is None:
        return 2
    print(f"Map_class: {map_cls.__module__}.{map_cls.__name__}")
    print(f"Map_signature: {_safe_signature(map_cls) or '(signature unavailable)'}")

    _print_basemap_shadowing(module)
    helpers_ok = _print_helper_modules()
    if args.backend == "folium":
        # Folium is an HTML-oriented backend and does not provide all
        # ipyleaflet widget helper modules/methods. Report those facts above
        # without failing the folium smoke when the folium Map itself works.
        helpers_ok = True
    _print_methods(map_cls)
    instance_ok = _instantiate_map(map_cls, args.skip_ee_init)

    if not helpers_ok or not instance_ok:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
