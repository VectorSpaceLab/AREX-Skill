#!/usr/bin/env python3
"""Check a Python environment for umap-learn and optional extras.

Examples:
  python check_umap_environment.py --json
  python check_umap_environment.py --check-plot --check-parametric --json
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from importlib import metadata


def module_status(name: str):
    try:
        module = importlib.import_module(name)
        return {"available": True, "version": getattr(module, "__version__", "available")}
    except Exception as exc:
        return {"available": False, "error": type(exc).__name__, "message": str(exc).splitlines()[0]}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect umap-learn installation and optional extras.")
    parser.add_argument("--check-plot", action="store_true", help="Check optional umap.plot dependencies.")
    parser.add_argument("--check-parametric", action="store_true", help="Check optional ParametricUMAP dependencies.")
    parser.add_argument("--json", action="store_true", help="Print JSON summary.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result: dict[str, object] = {"python": sys.version.split()[0], "distribution": {}, "imports": {}}

    try:
        dist_version = metadata.version("umap-learn")
        dist = metadata.distribution("umap-learn")
        result["distribution"] = {
            "name": dist.metadata.get("Name"),
            "version": dist_version,
            "requires_python": dist.metadata.get("Requires-Python"),
            "entry_points": [str(ep) for ep in dist.entry_points],
        }
    except metadata.PackageNotFoundError:
        result["distribution"] = {"error": "PackageNotFoundError", "message": "umap-learn distribution not found"}

    try:
        import umap
        result["imports"]["umap"] = {"available": True, "version": getattr(umap, "__version__", "unknown")}
        result["UMAP_signature"] = str(inspect.signature(umap.UMAP))
    except Exception as exc:
        result["imports"]["umap"] = {"available": False, "error": type(exc).__name__, "message": str(exc).splitlines()[0]}
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(result)
        return 1

    if args.check_plot:
        for name in ["pandas", "matplotlib", "datashader", "bokeh", "holoviews", "colorcet", "seaborn", "skimage", "dask"]:
            result["imports"][name] = module_status(name)
        try:
            import umap.plot  # noqa: F401
            result["imports"]["umap.plot"] = {"available": True}
        except Exception as exc:
            result["imports"]["umap.plot"] = {"available": False, "error": type(exc).__name__, "message": str(exc).splitlines()[0]}

    if args.check_parametric:
        for name in ["tensorflow", "keras"]:
            result["imports"][name] = module_status(name)
        try:
            from umap.parametric_umap import ParametricUMAP  # noqa: F401
            result["imports"]["umap.parametric_umap"] = {"available": True}
        except Exception as exc:
            result["imports"]["umap.parametric_umap"] = {"available": False, "error": type(exc).__name__, "message": str(exc).splitlines()[0]}

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(result)

    failed_base = not result["imports"].get("umap", {}).get("available")
    return 1 if failed_base else 0


if __name__ == "__main__":
    raise SystemExit(main())
