#!/usr/bin/env python3
"""Read-only AlpaSim environment and optional-backend diagnostic.

Run from any directory after installing the desired AlpaSim workspace extra:
    python path/to/check_env.py --json

The helper never downloads data, starts services, changes files, or handles
credentials. It reports missing optional imports instead of hiding them.
"""
from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from typing import Any


CORE_MODULES = (
    "alpasim_grpc",
    "alpasim_utils",
    "alpasim_runtime",
    "alpasim_wizard",
    "alpasim_plugins",
)
OPTIONAL_MODULES = (
    "torch",
    "warp",
    "torch_geometric",
    "torch_cluster",
    "alpasim_driver",
    "alpasim_trafficsim",
)


def _module_probe(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # report optional backend errors without a traceback
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "name": name,
        "ok": True,
        "version": getattr(module, "__version__", None),
    }


def _command_probe(name: str) -> dict[str, Any]:
    path = shutil.which(name)
    if path is None:
        return {"name": name, "available": False}
    try:
        result = subprocess.run(
            [name, "--version"], capture_output=True, text=True, timeout=5, check=False
        )
    except OSError as exc:
        return {"name": name, "available": True, "error": str(exc)}
    output = (result.stdout or result.stderr).strip().splitlines()
    return {"name": name, "available": True, "version": output[0] if output else None}


def collect() -> dict[str, Any]:
    report: dict[str, Any] = {
        "python": {"executable": sys.executable, "version": sys.version.split()[0]},
        "core_modules": [_module_probe(name) for name in CORE_MODULES],
        "optional_modules": [_module_probe(name) for name in OPTIONAL_MODULES],
        "commands": [_command_probe(name) for name in ("uv", "docker", "nvidia-smi", "cargo")],
    }
    torch = next((item for item in report["optional_modules"] if item["name"] == "torch"), None)
    if torch and torch["ok"]:
        try:
            module = importlib.import_module("torch")
            torch["cuda_available"] = bool(module.cuda.is_available())
            torch["cuda_version"] = module.version.cuda
        except Exception as exc:
            torch["cuda_probe_error"] = f"{type(exc).__name__}: {exc}"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()
    report = collect()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']['version']} ({report['python']['executable']})")
        for group in ("core_modules", "optional_modules"):
            for item in report[group]:
                suffix = "ok" if item["ok"] else item["error"]
                print(f"{item['name']}: {suffix}")
        for item in report["commands"]:
            print(f"{item['name']}: {'available' if item['available'] else 'missing'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
