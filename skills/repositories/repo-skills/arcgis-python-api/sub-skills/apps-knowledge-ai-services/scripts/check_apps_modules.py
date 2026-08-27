#!/usr/bin/env python3
"""Safely report ArcGIS app, graph, and AI module availability.

This script performs import/signature checks only. It does not connect to a
portal, call ArcGIS services, publish, clone, save, edit, or delete content.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import inspect
import json
import sys
from typing import Any, Dict

MODULES = [
    "arcgis",
    "arcgis.apps",
    "arcgis.apps.storymap",
    "arcgis.apps.expbuilder",
    "arcgis.apps.itemgraph",
    "arcgis.apps.hub",
    "arcgis.apps.survey123",
    "arcgis.apps.tracker",
    "arcgis.apps.workforce",
    "arcgis.apps.dashboard",
    "arcgis.apps.dashboards",
    "arcgis.graph",
    "arcgis.ai",
]
OPTIONAL_MODULES = {"arcgis.apps.dashboards", "arcgis.ai"}
SELECTED_SYMBOLS = {
    "arcgis.apps": [
        "build_collector_url",
        "build_explorer_url",
        "build_field_maps_url",
        "build_navigator_url",
        "build_survey123_url",
        "build_tracker_url",
        "build_workforce_url",
    ],
    "arcgis.apps.storymap": ["StoryMap", "Briefing", "Collection", "Text", "Image", "Video", "Timeline"],
    "arcgis.apps.expbuilder": ["WebExperience", "Templates"],
    "arcgis.apps.itemgraph": ["ItemGraph", "ItemNode", "create_dependency_graph", "load_from_file"],
    "arcgis.apps.hub": ["Hub"],
    "arcgis.apps.survey123": ["SurveyManager", "Survey"],
    "arcgis.apps.tracker": ["LocationTrackingManager", "TrackView", "TrackViewerManager", "MobileUserManager"],
    "arcgis.apps.workforce": ["create_project", "Project", "Assignment", "Worker", "Dispatcher"],
    "arcgis.apps.dashboard": ["Dashboard", "Header", "Indicator", "Details", "Gauge", "List", "PieChart", "SerialChart"],
    "arcgis.graph": ["KnowledgeGraph"],
    "arcgis.ai": ["analyze_image", "analyze_text", "translate", "AIUtilsResponse"],
}


def package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def import_module_record(name: str) -> Dict[str, Any]:
    record: Dict[str, Any] = {"ok": False, "optional": name in OPTIONAL_MODULES}
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001
        record["error_type"] = type(exc).__name__
        record["error"] = str(exc)
        return record

    record["ok"] = True
    record["exports_sample"] = [item for item in dir(module) if not item.startswith("_")][:40]
    selected: Dict[str, Any] = {}
    for symbol in SELECTED_SYMBOLS.get(name, []):
        if not hasattr(module, symbol):
            selected[symbol] = None
            continue
        obj = getattr(module, symbol)
        try:
            selected[symbol] = str(inspect.signature(obj))
        except Exception:
            selected[symbol] = "(signature unavailable)"
    if selected:
        record["selected"] = selected
    return record


def build_report() -> Dict[str, Any]:
    modules = {name: import_module_record(name) for name in MODULES}
    missing_modules = [name for name, record in modules.items() if not record["ok"]]
    required_failures = [name for name in missing_modules if name not in OPTIONAL_MODULES]
    return {
        "python": sys.version.split()[0],
        "packages": {
            "arcgis": package_version("arcgis"),
            "arcgis-mapping": package_version("arcgis-mapping"),
        },
        "modules": modules,
        "missing_modules": missing_modules,
        "required_failures": required_failures,
        "service_calls_made": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely probe ArcGIS app, graph, dashboard, and AI modules.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)
    report = build_report()

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print("ArcGIS apps/Knowledge/AI module probe")
        print("service_calls_made=False")
        for name, version in report["packages"].items():
            print(f"{name}: {version or 'MISSING'}")
        for name in MODULES:
            record = report["modules"][name]
            if record["ok"]:
                print(f"OK   {name}")
            else:
                tag = "OPTIONAL-MISSING" if record["optional"] else "FAIL"
                print(f"{tag} {name}: {record['error_type']}: {record['error']}")

    return 1 if report["required_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
