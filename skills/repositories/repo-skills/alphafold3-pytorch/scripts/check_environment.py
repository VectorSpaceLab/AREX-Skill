#!/usr/bin/env python3
"""Read-only AlphaFold 3 PyTorch environment and backend diagnostic.

This helper can run from any current directory. It checks installed metadata
and imports, optionally probes CUDA with one tiny allocation, and never installs
packages, downloads weights/data, writes files, launches a server, or runs a
model. Use it to separate an environment problem from an API or checkpoint
problem.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import platform
import sys
from typing import Any


CORE_IMPORTS = ("torch", "alphafold3_pytorch")
OPTIONAL_IMPORTS = ("Bio", "gemmi", "rdkit", "lightning", "gradio", "nimporter_plus")


def check_import(name: str) -> dict[str, Any]:
    result: dict[str, Any] = {"module": name, "ok": False}
    try:
        module = importlib.import_module(name)
        result["ok"] = True
        result["version"] = getattr(module, "__version__", None)
        result["file"] = getattr(module, "__file__", None)
    except Exception as exc:  # diagnostic output should identify, not hide, failures
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def collect(probe_cuda: bool) -> dict[str, Any]:
    report: dict[str, Any] = {
        "python": {"version": sys.version, "executable": sys.executable},
        "platform": {"system": platform.system(), "machine": platform.machine()},
        "distribution": {},
        "imports": [],
        "cuda": {"requested": probe_cuda, "available": False},
    }
    try:
        report["distribution"]["alphafold3-pytorch"] = importlib.metadata.version(
            "alphafold3-pytorch"
        )
    except importlib.metadata.PackageNotFoundError:
        report["distribution"]["alphafold3-pytorch"] = None

    report["imports"] = [check_import(name) for name in (*CORE_IMPORTS, *OPTIONAL_IMPORTS)]

    torch_result = next(item for item in report["imports"] if item["module"] == "torch")
    if torch_result["ok"]:
        torch = importlib.import_module("torch")
        report["torch"] = {
            "version": getattr(torch, "__version__", None),
            "cuda_build": getattr(getattr(torch, "version", None), "cuda", None),
        }
        if probe_cuda:
            report["cuda"]["available"] = bool(torch.cuda.is_available())
            report["cuda"]["device_count"] = int(torch.cuda.device_count())
            if report["cuda"]["available"]:
                report["cuda"]["device_name"] = torch.cuda.get_device_name(0)
                report["cuda"]["capability"] = list(torch.cuda.get_device_capability(0))
                try:
                    torch.empty((1,), device="cuda")
                    report["cuda"]["allocation"] = "ok"
                except Exception as exc:
                    report["cuda"]["allocation"] = f"{type(exc).__name__}: {exc}"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cuda", action="store_true", help="probe CUDA availability and one tiny allocation")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    report = collect(args.cuda)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(f"python: {report['python']['version'].split()[0]}")
        print(f"alphafold3-pytorch: {report['distribution']['alphafold3-pytorch'] or 'not installed'}")
        for item in report["imports"]:
            suffix = "" if item["ok"] else f" ({item.get('error', 'failed')})"
            print(f"import {item['module']}: {'ok' if item['ok'] else 'failed'}{suffix}")
        if args.cuda:
            print(f"cuda: {'available' if report['cuda']['available'] else 'unavailable'}")
            if "allocation" in report["cuda"]:
                print(f"cuda allocation: {report['cuda']['allocation']}")
    core_failed = [item for item in report["imports"] if item["module"] in CORE_IMPORTS and not item["ok"]]
    return 1 if core_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
