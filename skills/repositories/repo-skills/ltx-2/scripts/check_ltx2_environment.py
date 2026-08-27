#!/usr/bin/env python3
"""Inspect a Python environment for the LTX-2 packages and CUDA readiness.

Safe by default: imports packages, prints metadata, and performs a tiny CUDA
allocation when available. It does not download models, train, or generate
media.

Example:
    python check_ltx2_environment.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def _version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def _import_path(name: str) -> str | None:
    try:
        mod = __import__(name)
    except Exception:
        return None
    return getattr(mod, "__file__", None)


def _cuda_smoke() -> dict[str, object]:
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "error": f"torch import failed: {exc}"}

    info: dict[str, object] = {
        "torch": getattr(torch, "__version__", None),
        "cuda_runtime": getattr(torch.version, "cuda", None),
        "available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
    }
    if torch.cuda.is_available():
        try:
            info["device0_name"] = torch.cuda.get_device_name(0)
            info["device0_capability"] = torch.cuda.get_device_capability(0)
            tensor = torch.ones((1,), device="cuda")
            info["tiny_tensor_ok"] = bool(tensor.device.type == "cuda")
        except Exception as exc:  # noqa: BLE001
            info["error"] = str(exc)
    return info


def build_report() -> dict[str, object]:
    packages = {
        "ltx-core": _version("ltx-core"),
        "ltx-pipelines": _version("ltx-pipelines"),
        "ltx-trainer": _version("ltx-trainer"),
        "torch": _version("torch"),
        "transformers": _version("transformers"),
        "av": _version("av"),
        "openimageio": _version("openimageio"),
        "typer": _version("typer"),
    }
    imports = {
        "ltx_core": _import_path("ltx_core"),
        "ltx_pipelines": _import_path("ltx_pipelines"),
        "ltx_trainer": _import_path("ltx_trainer"),
    }
    return {
        "python": sys.version,
        "executable": sys.executable,
        "packages": packages,
        "imports": imports,
        "cuda": _cuda_smoke(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    args = parser.parse_args()
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(f"Python: {report['python']}")
        print(f"Executable: {report['executable']}")
        for name, value in report["packages"].items():
            print(f"{name}: {value}")
        for name, value in report["imports"].items():
            print(f"{name}: {value}")
        cuda = report["cuda"]
        print(f"CUDA available: {cuda.get('available')}")
        if cuda.get("available"):
            print(f"CUDA device count: {cuda.get('device_count')}")
            print(f"CUDA device0: {cuda.get('device0_name')} {cuda.get('device0_capability')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
