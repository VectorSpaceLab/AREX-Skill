#!/usr/bin/env python3
"""Check a Newton installation and optional Warp backends.

Run from any directory with the Python environment that should use Newton:

    python check_newton_env.py --require-cuda

The script imports only public packages and performs no downloads, training, or
repo-local file access.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from importlib.metadata import PackageNotFoundError, version


def _dist_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "not-installed"


def _optional_import(name: str) -> str:
    try:
        importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report import failures.
        return f"missing ({type(exc).__name__}: {exc})"
    return "available"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check public Newton imports, package versions, and Warp devices.")
    parser.add_argument("--require-cuda", action="store_true", help="Return non-zero if Warp cannot allocate on cuda:0.")
    parser.add_argument("--show-optional", action="store_true", help="Report common optional dependency modules.")
    args = parser.parse_args()

    print(f"python={sys.version.split()[0]}")
    print(f"distribution.newton={_dist_version('newton')}")
    print(f"distribution.warp-lang={_dist_version('warp-lang')}")

    try:
        import newton
        import warp as wp
    except ModuleNotFoundError as exc:
        print(f"ERROR: missing required package: {exc.name}")
        print("Install Newton with: pip install newton  (or pip install 'newton[examples]' for examples/viewers)")
        return 2

    print(f"newton.__version__={getattr(newton, '__version__', 'unknown')}")
    print(f"newton public modules={', '.join(m for m in ['actuators','controllers','geometry','ik','math','selection','sensors','solvers','usd','utils','viewer'] if hasattr(newton, m))}")

    try:
        wp.init()
        devices = [str(d) for d in wp.get_devices()]
        print("warp.devices=" + ", ".join(devices))
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: Warp initialized unsuccessfully: {type(exc).__name__}: {exc}")
        return 3

    for dev in ["cpu", "cuda:0"]:
        try:
            device = wp.get_device(dev)
            wp.zeros(1, dtype=float, device=device)
            print(f"device.{dev}=ok ({device.name})")
        except Exception as exc:  # noqa: BLE001
            print(f"device.{dev}=unavailable ({type(exc).__name__}: {exc})")
            if dev == "cuda:0" and args.require_cuda:
                return 4

    if args.show_optional:
        optional = {
            "mujoco": "newton[sim]",
            "mujoco_warp": "newton[sim]",
            "pxr": "newton[importers] or newton[docs]",
            "newton_usd_schemas": "newton[importers]",
            "trimesh": "newton[importers]",
            "open3d": "newton[importers] or newton[remesh] where wheels exist",
            "warp_nn": "newton[onnx]",
            "torch": "newton[torch-cu12] or newton[torch-cu13]",
            "pyglet": "newton[examples] or newton[rtx]",
            "rerun": "newton[notebook] or explicit rerun-sdk install",
            "viser": "newton[notebook]",
            "ovrtx": "newton[rtx]",
        }
        for module, extra in optional.items():
            print(f"optional.{module}={_optional_import(module)} ; install via {extra}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
