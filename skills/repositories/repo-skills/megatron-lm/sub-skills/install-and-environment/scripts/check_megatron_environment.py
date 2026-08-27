#!/usr/bin/env python3
"""Safe Megatron Core environment probe.

This script checks package metadata, imports, optional modules, and CUDA
availability without starting distributed training or reading a repository
checkout. It is intended for agents using the megatron-lm repo skill.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib import metadata


def _try_import(name: str) -> dict:
    try:
        mod = importlib.import_module(name)
    except Exception as exc:  # broad: report import diagnostics, do not hide them
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    version = getattr(mod, "__version__", None)
    return {"name": name, "ok": True, "version": version}


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe a Megatron Core Python environment.")
    parser.add_argument("--check-cuda", action="store_true", help="Require torch CUDA availability.")
    parser.add_argument(
        "--optional",
        nargs="*",
        default=[],
        help="Optional modules to import and report, e.g. transformer_engine apex modelopt.",
    )
    args = parser.parse_args()

    report: dict = {"python": sys.version, "executable": sys.executable, "checks": {}}

    try:
        report["distribution"] = {
            "name": "megatron-core",
            "version": metadata.version("megatron-core"),
            "requires": metadata.requires("megatron-core") or [],
        }
    except metadata.PackageNotFoundError as exc:
        report["distribution"] = {"name": "megatron-core", "ok": False, "error": str(exc)}

    imports = [_try_import("megatron.core"), _try_import("megatron.training")]
    report["checks"]["imports"] = imports

    torch_info: dict = {"import": _try_import("torch")}
    if torch_info["import"]["ok"]:
        import torch

        torch_info.update(
            {
                "torch_version": torch.__version__,
                "torch_cuda": getattr(torch.version, "cuda", None),
                "cuda_available": bool(torch.cuda.is_available()),
                "cuda_device_count": int(torch.cuda.device_count()),
            }
        )
        if torch.cuda.is_available():
            torch_info["device0"] = torch.cuda.get_device_name(0)
            torch_info["capability0"] = list(torch.cuda.get_device_capability(0))
            torch.empty((1,), device="cuda")
    report["checks"]["torch"] = torch_info

    report["checks"]["optional_imports"] = [_try_import(name) for name in args.optional]

    failed = False
    if not all(item["ok"] for item in imports):
        failed = True
    if args.check_cuda and not torch_info.get("cuda_available"):
        failed = True
        report["checks"]["cuda_required"] = "failed"
    elif args.check_cuda:
        report["checks"]["cuda_required"] = "passed"

    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
