#!/usr/bin/env python3
"""Check an environment for scvi-tools workflow readiness."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import sys
from typing import Any

MODULES = ["scvi", "anndata", "torch"]
OPTIONAL_MODULES = ["ray", "hyperopt", "huggingface_hub", "mlflow", "mudata"]
DISTS = ["scvi-tools", "anndata", "torch", "lightning", "scanpy", "pyro-ppl"]


def module_status(name: str) -> dict[str, Any]:
    try:
        importlib.import_module(name)
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    distribution = "scvi-tools" if name == "scvi" else name
    version = dist_status(distribution).get("version")
    return {"ok": True, "version": version}


def dist_status(name: str) -> dict[str, Any]:
    try:
        return {"ok": True, "version": metadata.version(name)}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def collect() -> dict[str, Any]:
    result: dict[str, Any] = {
        "python": sys.version.split()[0],
        "modules": {name: module_status(name) for name in MODULES},
        "optional_modules": {name: module_status(name) for name in OPTIONAL_MODULES},
        "distributions": {name: dist_status(name) for name in DISTS},
        "backend": {},
    }
    try:
        import torch

        result["backend"] = {
            "torch_version": torch.__version__,
            "cuda_build": torch.version.cuda,
            "cuda_available": torch.cuda.is_available(),
            "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        }
        if torch.cuda.is_available():
            result["backend"]["cuda_device_0"] = torch.cuda.get_device_name(0)
    except Exception as exc:
        result["backend"] = {"error": f"{type(exc).__name__}: {exc}"}
    return result


def print_text(result: dict[str, Any]) -> None:
    print(f"Python: {result['python']}")
    print("Required modules:")
    for name, status in result["modules"].items():
        suffix = status.get("version") or status.get("error")
        print(f"  {name}: {'ok' if status['ok'] else 'missing'} {suffix or ''}".rstrip())
    print("Distributions:")
    for name, status in result["distributions"].items():
        suffix = status.get("version") or status.get("error")
        print(f"  {name}: {'ok' if status['ok'] else 'missing'} {suffix}")
    backend = result.get("backend", {})
    print("Backend:")
    for key, value in backend.items():
        print(f"  {key}: {value}")
    print("Optional modules:")
    for name, status in result["optional_modules"].items():
        suffix = status.get("version") or status.get("error")
        print(f"  {name}: {'ok' if status['ok'] else 'missing'} {suffix or ''}".rstrip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)
    result = collect()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text(result)
    required_ok = all(status["ok"] for status in result["modules"].values())
    scvi_dist_ok = result["distributions"]["scvi-tools"]["ok"]
    return 0 if required_ok and scvi_dist_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
