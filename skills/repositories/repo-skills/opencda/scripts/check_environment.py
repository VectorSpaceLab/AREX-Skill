#!/usr/bin/env python3
"""Read-only OpenCDA environment probe.

Run from any directory. The probe reports package/API availability and optional
CARLA, SUMO, ScenarioRunner, and PyTorch signals; it never starts a simulator,
connects to a server, downloads models, or changes files.
"""

from __future__ import print_function

import argparse
import importlib
import importlib.util
import json
import os
import shutil
import sys


def probe_module(name):
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # optional modules can fail on native imports
        return {"available": False, "error": "%s: %s" % (type(exc).__name__, exc)}
    return {
        "available": True,
        "version": getattr(module, "__version__", None),
        "location": getattr(module, "__file__", None),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    modules = {}
    for name in (
        "opencda", "omegaconf", "numpy", "scipy", "matplotlib",
        "networkx", "cv2", "open3d", "shapely", "yaml", "carla",
        "torch", "traci", "sumolib", "scenario_runner",
    ):
        modules[name] = probe_module(name)

    executables = {name: shutil.which(name) for name in ("sumo", "netconvert")}
    result = {
        "python": {"version": sys.version, "executable": sys.executable},
        "modules": modules,
        "executables": executables,
        "environment": {
            "SUMO_HOME_set": bool(os.environ.get("SUMO_HOME")),
            "CARLA_HOME_set": bool(os.environ.get("CARLA_HOME")),
        },
        "safe": True,
        "note": "Availability is not proof of a live simulator, compatible map, model weights, or backend service.",
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("OpenCDA environment probe (read-only)")
        print("Python: %s" % sys.version.split()[0])
        for name, info in modules.items():
            print("%-18s %s" % (name, "available" if info["available"] else "missing"))
        for name, path in executables.items():
            print("%-18s %s" % (name, path or "missing"))
        print("SUMO_HOME set: %s" % result["environment"]["SUMO_HOME_set"])
        print(result["note"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
