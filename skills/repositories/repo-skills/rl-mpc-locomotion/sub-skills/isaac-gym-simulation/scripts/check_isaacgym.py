#!/usr/bin/env python3
"""Safe Isaac Gym/package/device diagnostic.

This script never acquires a gym, creates a simulation, starts a viewer, or
runs a repository example. It only probes importability and device visibility.
"""

from __future__ import print_function

import argparse
import importlib
import importlib.util
import json
import sys


def check_isaacgym():
    result = {
        "isaacgym": {"status": "missing", "gymapi": False, "gymtorch": False},
        "pytorch": {"status": "not_checked", "version": None, "cuda_build": None},
        "cuda": {"available": False, "device_count": 0, "devices": []},
        "backend_status": "BLOCKED_REQUIRED_BACKEND",
        "viewer_started": False,
        "simulation_started": False,
    }

    try:
        spec = importlib.util.find_spec("isaacgym")
    except Exception as exc:  # pragma: no cover - environment-specific
        spec = None
        result["isaacgym"]["probe_error"] = type(exc).__name__

    if spec is not None:
        result["isaacgym"]["status"] = "discoverable"
        for module_name, key in (("isaacgym.gymapi", "gymapi"),
                                 ("isaacgym.gymtorch", "gymtorch")):
            try:
                importlib.import_module(module_name)
                result["isaacgym"][key] = True
            except Exception as exc:  # pragma: no cover - environment-specific
                result["isaacgym"][key + "_error"] = type(exc).__name__
        if result["isaacgym"]["gymapi"] and result["isaacgym"]["gymtorch"]:
            result["isaacgym"]["status"] = "importable"

    try:
        import torch

        result["pytorch"] = {
            "status": "importable",
            "version": getattr(torch, "__version__", None),
            "cuda_build": getattr(getattr(torch, "version", None), "cuda", None),
        }
        try:
            available = bool(torch.cuda.is_available())
            count = int(torch.cuda.device_count()) if available else 0
            devices = []
            for index in range(count):
                try:
                    devices.append(torch.cuda.get_device_name(index))
                except Exception:
                    devices.append("unavailable")
            result["cuda"] = {
                "available": available,
                "device_count": count,
                "devices": devices,
            }
        except Exception as exc:  # pragma: no cover - environment-specific
            result["cuda"]["probe_error"] = type(exc).__name__
    except Exception as exc:  # pragma: no cover - environment-specific
        result["pytorch"] = {"status": "unavailable", "error": type(exc).__name__}

    if result["isaacgym"]["status"] == "importable":
        result["backend_status"] = "PREREQUISITE_IMPORTS_PASS_NATIVE_RUN_REQUIRED"
    return result


def print_human(result):
    isaac = result["isaacgym"]
    torch = result["pytorch"]
    cuda = result["cuda"]
    print("Isaac Gym status: {}".format(isaac["status"]))
    print("  gymapi import: {}".format("pass" if isaac["gymapi"] else "fail"))
    print("  gymtorch import: {}".format("pass" if isaac["gymtorch"] else "fail"))
    print("PyTorch status: {}".format(torch["status"]))
    if torch.get("version"):
        print("  version: {}".format(torch["version"]))
    if torch.get("cuda_build"):
        print("  CUDA build: {}".format(torch["cuda_build"]))
    print("CUDA available: {} ({} device(s))".format(
        cuda["available"], cuda["device_count"]))
    for index, device in enumerate(cuda.get("devices", [])):
        print("  device {}: {}".format(index, device))
    print("Viewer started: false")
    print("Simulation started: false")
    print("Backend verdict: {}".format(result["backend_status"]))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Probe Isaac Gym imports and PyTorch/CUDA without starting a viewer."
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    result = check_isaacgym()
    if args.json:
        print(json.dumps(result, sort_keys=True, indent=2))
    else:
        print_human(result)
    # An absent or partial vendor SDK is an intentional required-backend block.
    return 0 if result["backend_status"] != "BLOCKED_REQUIRED_BACKEND" else 2


if __name__ == "__main__":
    sys.exit(main())
