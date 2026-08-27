#!/usr/bin/env python3
"""Safe import/signature smoke for imagery and raster surfaces.

This script only imports modules and inspects callable signatures. It never
instantiates a GIS object, opens credentials, or calls image/raster services.
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from dataclasses import dataclass
from importlib import metadata
from typing import Any, Dict


@dataclass(frozen=True)
class Surface:
    module: str
    attr_path: str
    required: bool = True


SURFACES = [
    Surface("arcgis.raster", "ImageryLayer"),
    Surface("arcgis.raster", "ImageryLayer.save"),
    Surface("arcgis.raster", "ImageryLayer.draw_graph"),
    Surface("arcgis.raster.functions", "apply"),
    Surface("arcgis.raster.functions", "stretch"),
    Surface("arcgis.raster.functions", "extract_band"),
    Surface("arcgis.raster.functions", "band_arithmetic"),
    Surface("arcgis.raster.functions", "clip"),
    Surface("arcgis.raster.functions", "colormap"),
    Surface("arcgis.raster.functions", "savi"),
    Surface("arcgis.raster.functions", "ndvi", required=False),
    Surface("arcgis.raster.functions", "composite_band", required=False),
    Surface("arcgis.raster.analytics", "is_supported"),
    Surface("arcgis.raster.analytics", "copy_raster"),
    Surface("arcgis.raster.analytics", "create_image_collection"),
    Surface("arcgis.raster.analytics", "calculate_density"),
    Surface("arcgis.raster.analytics", "create_viewshed"),
    Surface("arcgis.raster.analytics", "interpolate_points"),
    Surface("arcgis.raster.analytics", "convert_feature_to_raster"),
    Surface("arcgis.raster.analytics", "convert_raster_to_feature"),
    Surface("arcgis.raster.analytics", "train_classifier"),
    Surface("arcgis.raster.analytics", "classify"),
    Surface("arcgis.raster.analytics", "segment"),
    Surface("arcgis.raster.analytics", "generate_raster", required=False),
    Surface("arcgis.raster.analytics", "add_image", required=False),
    Surface("arcgis.raster.orthomapping", "is_supported"),
    Surface("arcgis.raster.orthomapping", "query_camera_info"),
    Surface("arcgis.raster.orthomapping", "compute_sensor_model"),
    Surface("arcgis.raster.orthomapping", "compute_control_points"),
    Surface("arcgis.raster.orthomapping", "match_control_points"),
    Surface("arcgis.raster.orthomapping", "edit_control_points"),
    Surface("arcgis.raster.orthomapping", "query_control_points"),
    Surface("arcgis.raster.orthomapping", "compute_seamlines"),
    Surface("arcgis.raster.orthomapping", "generate_orthomosaic"),
    Surface("arcgis.raster.orthomapping", "generate_dem"),
    Surface("arcgis.raster.orthomapping", "generate_report"),
    Surface("arcgis.raster.orthomapping", "alter_processing_states"),
    Surface("arcgis.raster.orthomapping", "reset_image_collection"),
    Surface("arcgis.raster.orthomapping", "Project", required=False),
]


def package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def resolve(module_name: str, attr_path: str) -> Any:
    obj: Any = importlib.import_module(module_name)
    for part in attr_path.split("."):
        obj = getattr(obj, part)
    return obj


def surface_record(surface: Surface) -> Dict[str, Any]:
    qualname = f"{surface.module}.{surface.attr_path}"
    try:
        obj = resolve(surface.module, surface.attr_path)
        try:
            signature = str(inspect.signature(obj))
        except (TypeError, ValueError):
            signature = "<signature unavailable>"
        return {"ok": True, "required": surface.required, "qualname": qualname, "signature": signature}
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "required": surface.required,
            "qualname": qualname,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }


def build_report() -> Dict[str, Any]:
    surfaces = [surface_record(surface) for surface in SURFACES]
    required_failures = [r for r in surfaces if r["required"] and not r["ok"]]
    optional_missing = [r for r in surfaces if not r["required"] and not r["ok"]]
    return {
        "python": sys.version.split()[0],
        "packages": {"arcgis": package_version("arcgis")},
        "surfaces": surfaces,
        "required_failures": required_failures,
        "optional_missing": optional_missing,
        "service_calls_made": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely probe ArcGIS raster/imagery imports and signatures.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)
    report = build_report()

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("ArcGIS raster/imagery import probe")
        print("service_calls_made=False")
        print(f"arcgis: {report['packages']['arcgis'] or 'MISSING'}")
        for record in report["surfaces"]:
            if record["ok"]:
                print(f"OK   {record['qualname']}: {record['signature']}")
            else:
                tag = "FAIL" if record["required"] else "OPTIONAL-MISSING"
                print(f"{tag} {record['qualname']}: {record['error_type']}: {record['error']}")

    return 1 if report["required_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
