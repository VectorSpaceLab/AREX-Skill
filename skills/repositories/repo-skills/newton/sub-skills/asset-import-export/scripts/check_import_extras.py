#!/usr/bin/env python3
"""Check optional dependencies used by Newton asset import/export workflows."""

from __future__ import annotations

import argparse
import importlib

MODULES = {
    "pxr": "USD Python bindings from newton[importers] or newton[docs]",
    "newton_usd_schemas": "Newton USD schemas from newton[importers]",
    "mujoco": "MuJoCo from newton[sim]",
    "mujoco_warp": "MuJoCo Warp from newton[sim]",
    "requests": "URI and asset retrieval support from newton[importers]",
    "scipy": "mesh/convex hull utilities from newton[importers]",
    "trimesh": "mesh loading and V-HACD support from newton[importers]",
    "meshio": "fallback mesh loader from newton[importers]",
    "collada": "COLLADA support via pycollada from newton[importers]",
    "open3d": "Open3D remeshing/mesh processing from newton[importers] or newton[remesh]",
    "pyfqmr": "fast remeshing from newton[remesh]",
    "coacd": "convex decomposition from newton[importers] on supported Python versions",
}


def check(module: str) -> tuple[bool, str]:
    try:
        importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"
    return True, "available"


def main() -> int:
    parser = argparse.ArgumentParser(description="Report optional Newton asset/import/export dependencies.")
    parser.add_argument("--fail-missing", action="store_true", help="Return non-zero if any checked dependency is missing.")
    parser.add_argument("--module", action="append", choices=sorted(MODULES), help="Limit checks to selected module(s).")
    args = parser.parse_args()

    try:
        import newton
    except ModuleNotFoundError:
        print("ERROR: Newton is not importable. Install the base package before checking optional importers.")
        return 2

    selected = args.module or sorted(MODULES)
    missing = []
    print(f"newton={getattr(newton, '__version__', 'unknown')}")
    for module in selected:
        ok, detail = check(module)
        status = "ok" if ok else "missing"
        print(f"{module}: {status} - {detail} ; {MODULES[module]}")
        if not ok:
            missing.append(module)

    if missing:
        print("Missing optional modules do not break base Newton usage. Install the smallest extra that matches the asset workflow.")
        return 1 if args.fail_missing else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
