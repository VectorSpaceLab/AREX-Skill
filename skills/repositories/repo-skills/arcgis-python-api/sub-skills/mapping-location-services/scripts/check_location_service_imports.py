#!/usr/bin/env python3
"""Safe import/signature smoke for mapping and location services.

The script never creates a GIS connection, authenticates, or calls geocoding,
network analysis, or geoenrichment services.
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from importlib import metadata
from typing import Any, Dict

REQUIRED_MODULES = [
    "arcgis",
    "arcgis.map",
    "arcgis.map.symbols",
    "arcgis.map.renderers",
    "arcgis.map.popups",
    "arcgis.geocoding",
    "arcgis.network",
    "arcgis.network.analysis",
    "arcgis.geoenrichment",
]
OPTIONAL_MODULES = [
    "arcgis.map.map_widget",
    "arcgis.map.scene_widget",
    "arcgis.map.offline_mapping",
    "arcgis.map.smart_mapping",
    "arcgis.map.forms",
]
SIGNATURE_TARGETS = {
    "arcgis.map.Map": "arcgis.map:Map",
    "arcgis.map.Scene": "arcgis.map:Scene",
    "arcgis.geocoding.geocode": "arcgis.geocoding:geocode",
    "arcgis.geocoding.reverse_geocode": "arcgis.geocoding:reverse_geocode",
    "arcgis.geocoding.batch_geocode": "arcgis.geocoding:batch_geocode",
    "arcgis.geocoding.get_geocoders": "arcgis.geocoding:get_geocoders",
    "arcgis.network.analysis.find_routes": "arcgis.network.analysis:find_routes",
    "arcgis.network.analysis.generate_service_areas": "arcgis.network.analysis:generate_service_areas",
    "arcgis.network.analysis.find_closest_facilities": "arcgis.network.analysis:find_closest_facilities",
    "arcgis.network.analysis.generate_origin_destination_cost_matrix": "arcgis.network.analysis:generate_origin_destination_cost_matrix",
    "arcgis.network.analysis.solve_location_allocation": "arcgis.network.analysis:solve_location_allocation",
    "arcgis.network.analysis.solve_vehicle_routing_problem": "arcgis.network.analysis:solve_vehicle_routing_problem",
    "arcgis.geoenrichment.enrich": "arcgis.geoenrichment:enrich",
    "arcgis.geoenrichment.create_report": "arcgis.geoenrichment:create_report",
    "arcgis.geoenrichment.standard_geography_query": "arcgis.geoenrichment:standard_geography_query",
    "arcgis.geoenrichment.get_countries": "arcgis.geoenrichment:get_countries",
    "arcgis.geoenrichment.BufferStudyArea": "arcgis.geoenrichment:BufferStudyArea",
}


def package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def import_record(module_name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}
    return {"ok": True, "exports_sample": [n for n in dir(module) if not n.startswith("_")][:25]}


def resolve(spec: str) -> Any:
    module_name, attr_path = spec.split(":", 1)
    obj: Any = importlib.import_module(module_name)
    for part in attr_path.split("."):
        obj = getattr(obj, part)
    return obj


def signature_record(spec: str) -> Dict[str, Any]:
    try:
        obj = resolve(spec)
        return {"ok": True, "signature": str(inspect.signature(obj))}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}


def build_report() -> Dict[str, Any]:
    modules = {name: import_record(name) for name in REQUIRED_MODULES + OPTIONAL_MODULES}
    signatures = {label: signature_record(spec) for label, spec in SIGNATURE_TARGETS.items()}
    required_failures = [name for name in REQUIRED_MODULES if not modules[name]["ok"]]
    signature_failures = [name for name, rec in signatures.items() if not rec["ok"]]
    optional_missing = [name for name in OPTIONAL_MODULES if not modules[name]["ok"]]
    return {
        "python": sys.version.split()[0],
        "packages": {
            "arcgis": package_version("arcgis"),
            "arcgis-mapping": package_version("arcgis-mapping"),
        },
        "modules": modules,
        "signatures": signatures,
        "required_failures": required_failures,
        "signature_failures": signature_failures,
        "optional_missing": optional_missing,
        "service_calls_made": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely probe ArcGIS map/geocode/network/geoenrichment imports.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)
    report = build_report()

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("ArcGIS mapping/location service import probe")
        print("service_calls_made=False")
        print("Packages:")
        for name, value in report["packages"].items():
            print(f"  {name}: {value or 'MISSING'}")
        print("Required modules:")
        for name in REQUIRED_MODULES:
            print(f"  {name}: {'OK' if report['modules'][name]['ok'] else 'FAIL'}")
        print("Optional modules:")
        for name in OPTIONAL_MODULES:
            rec = report["modules"][name]
            status = "OK" if rec["ok"] else f"MISSING {rec['error_type']}: {rec['error']}"
            print(f"  {name}: {status}")
        if report["signature_failures"]:
            print("Signature failures:")
            for label in report["signature_failures"]:
                print(f"  {label}: {report['signatures'][label]}")

    return 1 if report["required_failures"] or report["signature_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
