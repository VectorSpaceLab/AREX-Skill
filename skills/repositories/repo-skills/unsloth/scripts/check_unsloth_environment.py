#!/usr/bin/env python3
"""Safe Unsloth environment checker.

This script inspects package metadata, CLI availability, optional backend
packages, and torch CUDA state. It does not load models, download weights,
start Studio, train, convert checkpoints, or contact network services.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from typing import Any


PACKAGES = [
    "unsloth",
    "unsloth_zoo",
    "torch",
    "transformers",
    "trl",
    "peft",
    "datasets",
    "accelerate",
    "bitsandbytes",
    "xformers",
    "triton",
    "torchvision",
]

MODULES = {
    "unsloth": "unsloth",
    "unsloth_zoo": "unsloth_zoo",
    "torch": "torch",
    "transformers": "transformers",
    "trl": "trl",
    "peft": "peft",
    "datasets": "datasets",
    "accelerate": "accelerate",
    "bitsandbytes": "bitsandbytes",
    "xformers": "xformers",
    "triton": "triton",
    "torchvision": "torchvision",
}


def package_version(name: str) -> dict[str, Any]:
    try:
        return {"installed": True, "version": metadata.version(name)}
    except metadata.PackageNotFoundError:
        return {"installed": False, "version": None}


def import_probe(module: str, *, import_unsloth: bool) -> dict[str, Any]:
    if module == "unsloth" and not import_unsloth:
        return {"checked": False, "reason": "skipped by default to avoid import-time patch/probe side effects"}
    try:
        imported = importlib.import_module(module)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"checked": True, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "checked": True,
        "ok": True,
        "version": getattr(imported, "__version__", None),
    }


def torch_probe() -> dict[str, Any]:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - depends on user env
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    payload: dict[str, Any] = {
        "ok": True,
        "version": getattr(torch, "__version__", None),
        "cuda_runtime": getattr(getattr(torch, "version", None), "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()),
    }
    if torch.cuda.is_available() and torch.cuda.device_count():
        payload["device0"] = torch.cuda.get_device_name(0)
        payload["capability0"] = list(torch.cuda.get_device_capability(0))
    return payload


def cli_probe(command: str) -> dict[str, Any]:
    exe = shutil.which(command)
    if exe is None:
        return {"available": False, "path": None}
    try:
        result = subprocess.run(
            [exe, "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=False,
        )
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"available": True, "path": exe, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    output = (result.stdout or result.stderr or "").splitlines()
    return {
        "available": True,
        "path": exe,
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "first_lines": output[:12],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect an Unsloth environment safely.")
    parser.add_argument("--import-unsloth", action="store_true", help="Also import unsloth; this may trigger patch/backend probes.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary.")
    args = parser.parse_args()

    payload = {
        "python": sys.version.split()[0],
        "packages": {name: package_version(name) for name in PACKAGES},
        "imports": {name: import_probe(module, import_unsloth=args.import_unsloth) for name, module in MODULES.items()},
        "torch": torch_probe(),
        "cli": {"unsloth": cli_probe("unsloth")},
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Python: {payload['python']}")
        print("Packages:")
        for name, info in payload["packages"].items():
            status = info["version"] if info["installed"] else "missing"
            print(f"  - {name}: {status}")
        print("Torch:")
        for key, value in payload["torch"].items():
            print(f"  - {key}: {value}")
        cli = payload["cli"]["unsloth"]
        print(f"CLI unsloth: {'available' if cli['available'] else 'missing'}")
        if not args.import_unsloth:
            print("Root unsloth import skipped; rerun with --import-unsloth when import-time probes are acceptable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
