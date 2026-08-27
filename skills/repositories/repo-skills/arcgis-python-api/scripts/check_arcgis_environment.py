#!/usr/bin/env python3
"""Safe ArcGIS API for Python environment probe.

This helper verifies local imports, package versions, and selected public
signatures without opening ArcGIS credentials, contacting online services,
downloading data, training models, or mutating portal content.

Example:
  python scripts/check_arcgis_environment.py --json
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from importlib.metadata import PackageNotFoundError, version as dist_version
from typing import Any, Dict

REQUIRED_DISTS = ["arcgis", "arcgis-mapping"]
CORE_MODULES = [
    "arcgis",
    "arcgis.gis",
    "arcgis.features",
    "arcgis.geometry",
    "arcgis.geocoding",
    "arcgis.map",
    "arcgis.map.symbols",
    "arcgis.map.renderers",
    "arcgis.layers",
    "arcgis.raster",
    "arcgis.raster.functions",
    "arcgis.raster.analytics",
    "arcgis.raster.orthomapping",
    "arcgis.network",
    "arcgis.network.analysis",
    "arcgis.geoenrichment",
    "arcgis.apps",
    "arcgis.apps.storymap",
    "arcgis.apps.expbuilder",
    "arcgis.apps.itemgraph",
    "arcgis.graph",
    "arcgis.geoprocessing",
]
OPTIONAL_MODULES = [
    "arcgis.learn",
    "arcgis.apps.dashboard",
    "arcgis.apps.dashboards",
    "arcgis.ai",
    "torch",
    "torchvision",
]
SIGNATURE_TARGETS = {
    "arcgis.gis.GIS": "arcgis.gis:GIS",
    "arcgis.gis.Item": "arcgis.gis:Item",
    "arcgis.features.FeatureLayer": "arcgis.features:FeatureLayer",
    "arcgis.features.FeatureSet": "arcgis.features:FeatureSet",
    "arcgis.geometry.Geometry": "arcgis.geometry:Geometry",
    "arcgis.geocoding.geocode": "arcgis.geocoding:geocode",
    "arcgis.geocoding.reverse_geocode": "arcgis.geocoding:reverse_geocode",
    "arcgis.geoenrichment.enrich": "arcgis.geoenrichment:enrich",
    "arcgis.network.analysis.find_routes": "arcgis.network.analysis:find_routes",
    "arcgis.raster.ImageryLayer": "arcgis.raster:ImageryLayer",
    "arcgis.raster.analytics.copy_raster": "arcgis.raster.analytics:copy_raster",
    "arcgis.map.Map": "arcgis.map:Map",
    "arcgis.apps.storymap.StoryMap": "arcgis.apps.storymap:StoryMap",
    "arcgis.apps.expbuilder.WebExperience": "arcgis.apps.expbuilder:WebExperience",
    "arcgis.apps.itemgraph.ItemGraph": "arcgis.apps.itemgraph:ItemGraph",
}


def package_version(name: str) -> str | None:
    try:
        return dist_version(name)
    except PackageNotFoundError:
        return None


def import_record(name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - report all import failures.
        return {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}
    record: Dict[str, Any] = {"ok": True}
    if hasattr(module, "__version__"):
        record["version"] = str(getattr(module, "__version__"))
    return record


def signature_record(label: str, spec: str) -> Dict[str, Any]:
    module_name, attr = spec.split(":", 1)
    try:
        module = importlib.import_module(module_name)
        obj = getattr(module, attr)
        return {"ok": True, "signature": str(inspect.signature(obj))}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}


def tiny_geometry_smoke() -> Dict[str, Any]:
    try:
        from arcgis.features import Feature, FeatureSet
        from arcgis.geometry import Geometry

        point = Geometry({"x": 1, "y": 2, "spatialReference": {"wkid": 4326}})
        feature = Feature(geometry=point, attributes={"name": "demo"})
        fset = FeatureSet([feature])
        return {
            "ok": True,
            "geometry_type": getattr(point, "geometry_type", None),
            "feature_count": len(fset.features),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}


def build_report(include_optional: bool = True) -> Dict[str, Any]:
    modules = {name: import_record(name) for name in CORE_MODULES}
    if include_optional:
        modules.update({name: import_record(name) for name in OPTIONAL_MODULES})
    return {
        "python": sys.version.split()[0],
        "packages": {name: package_version(name) for name in REQUIRED_DISTS},
        "modules": modules,
        "signatures": {label: signature_record(label, spec) for label, spec in SIGNATURE_TARGETS.items()},
        "tiny_geometry_smoke": tiny_geometry_smoke(),
        "service_calls_made": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely probe ArcGIS API imports and signatures.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human-readable summary.")
    parser.add_argument(
        "--no-optional",
        action="store_true",
        help="Skip optional import probes such as arcgis.learn, torch, dashboards, and arcgis.ai.",
    )
    args = parser.parse_args(argv)

    report = build_report(include_optional=not args.no_optional)
    required_ok = all(v for v in report["packages"].values()) and all(
        report["modules"][m]["ok"] for m in CORE_MODULES
    ) and bool(report["tiny_geometry_smoke"].get("ok"))

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("ArcGIS API for Python environment probe")
        print("service_calls_made=False")
        print("Packages:")
        for name, version in report["packages"].items():
            print(f"  {name}: {version or 'MISSING'}")
        print("Core modules:")
        for name in CORE_MODULES:
            status = "OK" if report["modules"][name]["ok"] else "FAIL"
            print(f"  {name}: {status}")
        optional_names = [name for name in OPTIONAL_MODULES if name in report["modules"]]
        if optional_names:
            print("Optional modules:")
            for name in optional_names:
                record = report["modules"][name]
                if record["ok"]:
                    print(f"  {name}: OK")
                else:
                    print(f"  {name}: MISSING {record['error_type']}: {record['error']}")
        smoke = report["tiny_geometry_smoke"]
        print(f"Tiny geometry smoke: {'OK' if smoke.get('ok') else 'FAIL'} {smoke}")

    return 0 if required_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
