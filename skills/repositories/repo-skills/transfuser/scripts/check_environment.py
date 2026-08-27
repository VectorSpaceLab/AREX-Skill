#!/usr/bin/env python3
"""Read-only TransFuser environment probe.

Reports package/CUDA/CARLA availability without importing the project model,
starting CARLA, downloading assets, or changing files. Run from any directory.
"""
from __future__ import print_function

import argparse
import importlib
import json
import os
import platform
import sys


PACKAGES = (
    "torch",
    "torchvision",
    "mmcv",
    "mmdet",
    "mmseg",
    "mmcls",
    "torch_scatter",
    "timm",
    "numpy",
    "cv2",
    "PIL",
    "ujson",
    "skimage",
)


def probe():
    result = {
        "python": {"version": sys.version.split()[0], "executable": sys.executable},
        "platform": {"system": platform.system(), "machine": platform.machine()},
        "packages": {},
        "cuda": {"available": False, "device_count": 0},
        "carla": {"available": False},
        "warnings": [],
    }
    for name in PACKAGES:
        try:
            module = importlib.import_module(name)
            result["packages"][name] = {
                "available": True,
                "version": getattr(module, "__version__", None),
            }
        except Exception as exc:  # diagnostic output should not hide one failure
            result["packages"][name] = {
                "available": False,
                "error": "{}: {}".format(type(exc).__name__, str(exc)),
            }

    torch = None
    try:
        torch = importlib.import_module("torch")
        result["cuda"].update({
            "available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()),
            "torch_version": getattr(torch, "__version__", None),
            "torch_cuda": getattr(torch.version, "cuda", None),
        })
        if torch.cuda.is_available():
            device = torch.cuda.current_device()
            result["cuda"].update({
                "current_device": int(device),
                "device_name": torch.cuda.get_device_name(device),
                "capability": list(torch.cuda.get_device_capability(device)),
            })
            try:
                torch.empty((1,), device="cuda")
                result["cuda"]["allocation"] = "passed"
            except Exception as exc:
                result["cuda"]["allocation"] = "failed: {}: {}".format(type(exc).__name__, exc)
                result["warnings"].append("CUDA is visible but a tiny allocation failed.")
    except Exception as exc:
        result["cuda"]["error"] = "{}: {}".format(type(exc).__name__, str(exc))

    try:
        carla = importlib.import_module("carla")
        result["carla"] = {
            "available": True,
            "version": getattr(carla, "__version__", None),
        }
    except Exception as exc:
        result["carla"]["error"] = "{}: {}".format(type(exc).__name__, str(exc))
        result["warnings"].append("CARLA Python API is unavailable; simulation is not verified.")

    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    result = probe()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Python: {}".format(result["python"]["version"]))
        print("CUDA: {} ({} device(s))".format(result["cuda"]["available"], result["cuda"]["device_count"]))
        print("CARLA Python API: {}".format(result["carla"]["available"]))
        for name, info in sorted(result["packages"].items()):
            state = "available" if info["available"] else "missing/broken"
            print("{}: {}".format(name, state))
        for warning in result["warnings"]:
            print("WARNING: {}".format(warning))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
