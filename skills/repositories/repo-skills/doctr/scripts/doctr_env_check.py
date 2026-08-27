#!/usr/bin/env python3
"""Safe docTR environment diagnostic.

Checks python-doctr metadata/imports, the installed doctr-cli entry point, and
optional PyTorch CPU/CUDA/MPS backend state. It never downloads model weights,
loads user documents, starts services, or modifies the environment.

Examples:
  python scripts/doctr_env_check.py
  python scripts/doctr_env_check.py --json
  python scripts/doctr_env_check.py --json --probe-gpu-commands
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any


def _check_import(name: str) -> dict[str, Any]:
    try:
        mod = importlib.import_module(name)
        return {"name": name, "ok": True, "file": getattr(mod, "__file__", None)}
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _run_short(cmd: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        return {
            "command": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip().splitlines()[:40],
            "stderr": proc.stderr.strip().splitlines()[:40],
        }
    except FileNotFoundError:
        return {"command": cmd, "returncode": None, "error": "executable not found"}
    except subprocess.TimeoutExpired:
        return {"command": cmd, "returncode": None, "error": f"timed out after {timeout}s"}


def collect(probe_gpu_commands: bool = False) -> dict[str, Any]:
    report: dict[str, Any] = {
        "python": {"executable": sys.executable, "version": sys.version},
        "metadata": {},
        "imports": [],
        "cli": {},
        "torch": {},
        "external_commands": {},
    }

    for dist in ["python-doctr", "torch", "torchvision", "onnx", "opencv-python", "pypdfium2"]:
        try:
            report["metadata"][dist] = metadata.version(dist)
        except metadata.PackageNotFoundError:
            report["metadata"][dist] = None

    for mod in ["doctr", "doctr.io", "doctr.models", "doctr.datasets", "doctr.transforms", "doctr.contrib"]:
        report["imports"].append(_check_import(mod))

    cli_path = shutil.which("doctr-cli")
    if not cli_path:
        sibling = Path(sys.executable).resolve().parent / "doctr-cli"
        if sibling.exists():
            cli_path = str(sibling)
    report["cli"]["path"] = cli_path
    if cli_path:
        report["cli"]["help"] = _run_short([cli_path, "--help"])

    torch_info: dict[str, Any] = {}
    try:
        import torch

        torch_info["ok"] = True
        torch_info["version"] = getattr(torch, "__version__", None)
        torch_info["cuda_version"] = getattr(torch.version, "cuda", None)
        torch_info["cuda_available"] = bool(torch.cuda.is_available())
        torch_info["cuda_device_count"] = int(torch.cuda.device_count()) if hasattr(torch.cuda, "device_count") else 0
        if torch_info["cuda_available"]:
            try:
                torch_info["cuda_device_0"] = torch.cuda.get_device_name(0)
                torch_info["cuda_capability_0"] = torch.cuda.get_device_capability(0)
            except Exception as exc:  # pragma: no cover
                torch_info["cuda_device_error"] = f"{type(exc).__name__}: {exc}"
        torch_info["mps_available"] = bool(getattr(getattr(torch, "backends", None), "mps", None) and torch.backends.mps.is_available())
        cpu_tensor = torch.empty((1,), device="cpu")
        torch_info["cpu_tensor"] = str(cpu_tensor.device)
    except Exception as exc:  # pragma: no cover - diagnostic path
        torch_info["ok"] = False
        torch_info["error"] = f"{type(exc).__name__}: {exc}"
    report["torch"] = torch_info

    if probe_gpu_commands:
        for cmd in (["nvidia-smi"], ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"], ["nvcc", "--version"]):
            report["external_commands"][" ".join(cmd)] = _run_short(cmd, timeout=15)

    report["ok"] = bool(
        report["metadata"].get("python-doctr")
        and any(item["name"] == "doctr" and item["ok"] for item in report["imports"])
        and report["cli"].get("path")
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a docTR/python-doctr installation without running OCR.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--probe-gpu-commands", action="store_true", help="Also run nvidia-smi/nvcc probes when available.")
    args = parser.parse_args()

    report = collect(probe_gpu_commands=args.probe_gpu_commands)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"python: {report['python']['version'].split()[0]} ({report['python']['executable']})")
        print(f"python-doctr: {report['metadata'].get('python-doctr')}")
        for item in report["imports"]:
            status = "ok" if item["ok"] else f"FAIL {item.get('error')}"
            print(f"import {item['name']}: {status}")
        print(f"doctr-cli: {report['cli'].get('path') or 'missing'}")
        torch_info = report["torch"]
        if torch_info.get("ok"):
            print(
                "torch: {version} cuda={cuda_version} cuda_available={cuda_available} "
                "devices={cuda_device_count} mps={mps_available}".format(**torch_info)
            )
        else:
            print(f"torch: FAIL {torch_info.get('error')}")
        print(f"overall: {'ok' if report['ok'] else 'not ready'}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
