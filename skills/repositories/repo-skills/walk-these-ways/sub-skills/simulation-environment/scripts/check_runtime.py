#!/usr/bin/env python3
"""Report package, backend, and Go1 asset prerequisites without side effects.

No repository module is imported. Missing Isaac Gym/CUDA is reported as a
finding rather than an error unless the corresponding --require flag is used.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

URDF = Path("resources/robots/go1/urdf/go1.urdf")
ACTUATOR = Path("resources/actuator_nets/unitree_go1.pt")
MESHES = [
    Path("resources/robots/go1/meshes/trunk.stl"),
    Path("resources/robots/go1/meshes/hip.stl"),
    Path("resources/robots/go1/meshes/thigh.stl"),
    Path("resources/robots/go1/meshes/thigh_mirror.stl"),
    Path("resources/robots/go1/meshes/calf.stl"),
]


def _module(name: str) -> Dict[str, Any]:
    try:
        spec = importlib.util.find_spec(name)
    except (ImportError, ModuleNotFoundError, ValueError) as exc:
        return {"available": False, "error": "%s: %s" % (type(exc).__name__, exc)}
    return {"available": spec is not None}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Walk These Ways prerequisite report")
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="checkout root used only for asset checks")
    parser.add_argument("--require-isaacgym", action="store_true")
    parser.add_argument("--require-cuda", action="store_true")
    parser.add_argument("--strict-assets", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = args.repo_root.expanduser().resolve()
    if not root.is_dir():
        parser.error("--repo-root is not a directory: %s" % root)

    packages: Dict[str, Any] = {}
    for distribution in ("go1_gym", "torch", "numpy", "params-proto"):
        try:
            packages[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            packages[distribution] = None

    modules = {name: _module(name) for name in ("go1_gym", "torch", "isaacgym")}
    cuda: Dict[str, Any] = {"available": False, "reason": "torch not importable or CUDA status not queried"}
    if modules["torch"].get("available"):
        try:
            import torch
            cuda = {"available": bool(torch.cuda.is_available()), "device_count": int(torch.cuda.device_count()), "torch": torch.__version__}
        except Exception as exc:  # optional diagnostic must remain readable
            cuda = {"available": False, "error": "%s: %s" % (type(exc).__name__, exc)}

    assets = {}
    for relative in [URDF] + MESHES + [ACTUATOR]:
        assets[str(relative)] = (root / relative).is_file()
    required_assets = [str(URDF)] + [str(mesh) for mesh in MESHES]
    missing_required = [path for path in required_assets if not assets[path]]
    result = {
        "python": sys.version.split()[0],
        "packages": packages,
        "modules": modules,
        "torch_cuda": cuda,
        "assets": assets,
        "missing_required_assets": missing_required,
        "optional_actuator_asset_present": assets[str(ACTUATOR)],
        "scope": "Read-only static/prerequisite check; no Isaac Gym simulation, training, networking, or file mutation was performed.",
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Walk These Ways prerequisite report (READ-ONLY)")
        print("Python: %s" % result["python"])
        print("Packages: %s" % packages)
        print("isaacgym available: %s" % modules["isaacgym"].get("available"))
        print("torch CUDA: %s" % cuda)
        for path, present in assets.items():
            print("asset %s: %s" % (path, "present" if present else "MISSING"))
        print(result["scope"])
    failed = False
    if args.require_isaacgym and not modules["isaacgym"].get("available"):
        failed = True
    if args.require_cuda and not cuda.get("available"):
        failed = True
    if args.strict_assets and missing_required:
        failed = True
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
