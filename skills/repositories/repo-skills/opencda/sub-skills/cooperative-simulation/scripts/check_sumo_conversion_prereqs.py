#!/usr/bin/env python3
"""Read-only preflight for an OpenCDA SUMO map directory.

This checker inspects paths, XML references, environment variables, executable
availability, and Python module discovery. It never starts SUMO, TraCI, CARLA,
ScenarioRunner, or netconvert and never writes to the inspected directory.
"""

from __future__ import print_function

import argparse
import importlib.util
import json
import os
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


class Report(object):
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.checks = []

    def check(self, name, status, detail):
        item = {"name": name, "status": status, "detail": detail}
        self.checks.append(item)
        if status == "error":
            self.errors.append(item)
        elif status == "warning":
            self.warnings.append(item)

    def as_dict(self, directory, basename):
        return {
            "directory": str(directory),
            "basename": basename,
            "ok": not self.errors,
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "checks": self.checks,
        }


def _module_available(name, extra_paths=()):
    """Find a module without importing or mutating sys.path."""
    if importlib.util.find_spec(name) is not None:
        return True
    for root in extra_paths:
        candidate = Path(root) / name
        if (candidate / "__init__.py").is_file() or (candidate.with_suffix(".py")).is_file():
            return True
    return False


def _resolve_from_config(config_path, value):
    return (config_path.parent / value).resolve()


def _split_route_files(value):
    # SUMO accepts a semicolon-separated list for route-files.
    return [part.strip() for part in value.split(";") if part.strip()]


def inspect(directory, basename=None):
    directory = Path(directory).expanduser().resolve()
    report = Report()
    if not directory.is_dir():
        report.check("map directory", "error", "directory does not exist: %s" % directory)
        return report, directory, basename or directory.name

    basename = basename or directory.name
    config = directory / (basename + ".sumocfg")
    network = directory / (basename + ".net.xml")
    routes = directory / (basename + ".rou.xml")
    for label, path in (("sumocfg", config), ("net.xml", network), ("rou.xml", routes)):
        status = "ok" if path.is_file() else "error"
        report.check(label, status, str(path))

    sumo_home = os.environ.get("SUMO_HOME")
    tools = Path(sumo_home).expanduser() / "tools" if sumo_home else None
    if sumo_home:
        report.check("SUMO_HOME", "ok" if Path(sumo_home).is_dir() else "error", sumo_home)
    else:
        report.check("SUMO_HOME", "error", "environment variable is not set")

    for executable in ("sumo", "netconvert"):
        found = shutil.which(executable)
        if not found and sumo_home:
            candidate = Path(sumo_home) / "bin" / executable
            if candidate.is_file() and os.access(str(candidate), os.X_OK):
                found = str(candidate)
        report.check("executable:%s" % executable, "ok" if found else "error", found or "not found")

    extra = (str(tools),) if tools else ()
    for module in ("traci", "sumolib"):
        available = _module_available(module, extra)
        report.check("python:%s" % module, "ok" if available else "error", "available" if available else "not found")

    if config.is_file():
        try:
            root = ET.parse(str(config)).getroot()
            net_tag = root.find("./input/net-file")
            route_tag = root.find("./input/route-files")
            if net_tag is None or not net_tag.get("value"):
                report.check("sumocfg net-file", "error", "missing <input><net-file value=...>")
            else:
                ref = _resolve_from_config(config, net_tag.get("value"))
                status = "ok" if ref.is_file() else "error"
                report.check("sumocfg net-file", status, str(ref))
                if ref.name != network.name:
                    report.check("network basename", "warning", "%s references %s (expected %s)" % (config.name, ref.name, network.name))

            if route_tag is None or not route_tag.get("value"):
                report.check("sumocfg route-files", "error", "missing <input><route-files value=...>")
            else:
                refs = []
                for value in _split_route_files(route_tag.get("value")):
                    ref = _resolve_from_config(config, value)
                    refs.append(str(ref))
                    report.check("sumocfg route-file", "ok" if ref.is_file() else "error", str(ref))
                if routes.name not in [Path(item).name for item in refs]:
                    report.check("route basename", "warning", "%s does not reference %s" % (config.name, routes.name))
        except (ET.ParseError, OSError) as exc:
            report.check("sumocfg XML", "error", str(exc))

    return report, directory, basename


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_directory", help="directory containing the SUMO map files")
    parser.add_argument("--basename", help="map basename; defaults to directory name")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)

    report, directory, basename = inspect(args.map_directory, args.basename)
    payload = report.as_dict(directory, basename)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("SUMO preflight: %s (%s)" % ("PASS" if payload["ok"] else "FAIL", directory))
        for item in payload["checks"]:
            print("[%s] %s: %s" % (item["status"].upper(), item["name"], item["detail"]))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
