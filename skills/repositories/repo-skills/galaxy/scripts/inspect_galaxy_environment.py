#!/usr/bin/env python3
"""Read-only Galaxy package-layout and import diagnostic helper.

This helper prints Python/package/import facts for a Galaxy-oriented environment.
It does not install packages, start services, build the client, contact network
services, or mutate files.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import platform
import sys
from typing import Any


DEFAULT_MODULES = [
    "galaxy.version",
    "galaxy.config",
    "galaxy.config.schema",
    "galaxy.tool_util.verify.script",
    "galaxy.tool_util.validate_test_format",
    "galaxy.tool_util.upgrade.script",
    "galaxy.webapps.openapi",
]

DEFAULT_DISTS = [
    "galaxy",
    "galaxy-util",
    "galaxy-config",
    "galaxy-schema",
    "galaxy-tool-util",
    "galaxy-tool-util-models",
    "galaxy-app",
    "galaxy-tool-shed",
    "galaxy-web-client",
]


def import_status(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic output should report any import failure
        return {"module": module_name, "ok": False, "error_type": type(exc).__name__, "error": str(exc)}
    result: dict[str, Any] = {"module": module_name, "ok": True}
    module_file = getattr(module, "__file__", None)
    if module_file:
        result["file"] = module_file
    if module_name == "galaxy.version":
        result["version"] = getattr(module, "VERSION", None)
    return result


def distribution_status(dist_name: str) -> dict[str, Any]:
    try:
        version = metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return {"distribution": dist_name, "installed": False}
    return {"distribution": dist_name, "installed": True, "version": version}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect a Galaxy-oriented Python environment without side effects.")
    parser.add_argument("--module", action="append", dest="modules", help="Module to import. May be supplied multiple times.")
    parser.add_argument("--distribution", action="append", dest="dists", help="Distribution metadata name to inspect. May be supplied multiple times.")
    parser.add_argument("--expected-version", help="Expected galaxy.version.VERSION value for staleness checks.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    modules = args.modules or DEFAULT_MODULES
    dists = args.dists or DEFAULT_DISTS
    imports = [import_status(module_name) for module_name in modules]
    distributions = [distribution_status(dist_name) for dist_name in dists]
    galaxy_version = next((item.get("version") for item in imports if item.get("module") == "galaxy.version" and item.get("ok")), None)
    version_matches = None
    if args.expected_version:
        version_matches = galaxy_version == args.expected_version

    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "imports": imports,
        "distributions": distributions,
        "galaxy_version": galaxy_version,
        "expected_version": args.expected_version,
        "version_matches": version_matches,
        "notes": [
            "This helper is read-only and does not prove a full Galaxy service can start.",
            "Missing optional imports may be acceptable when the selected workflow does not need that package.",
            "Use the focused sub-skill for config, API, tools/workflows, data/storage, Tool Shed, or client diagnostics.",
        ],
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        print(f"Platform: {report['platform']}")
        if args.expected_version:
            status = "MATCH" if version_matches else "DIFFERS"
            print(f"Galaxy source version: {galaxy_version!r} ({status}; expected {args.expected_version!r})")
        elif galaxy_version:
            print(f"Galaxy source version: {galaxy_version}")
        print("\nImports:")
        for item in imports:
            if item["ok"]:
                suffix = f" version={item['version']}" if "version" in item else ""
                print(f"  OK   {item['module']}{suffix}")
            else:
                print(f"  FAIL {item['module']}: {item['error_type']}: {item['error']}")
        print("\nDistributions:")
        for item in distributions:
            if item["installed"]:
                print(f"  OK   {item['distribution']}=={item['version']}")
            else:
                print(f"  MISS {item['distribution']}")
        print("\nNotes:")
        for note in report["notes"]:
            print(f"  - {note}")

    failed_required = [item for item in imports if not item["ok"] and item["module"] in (args.modules or [])]
    if failed_required or version_matches is False:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
