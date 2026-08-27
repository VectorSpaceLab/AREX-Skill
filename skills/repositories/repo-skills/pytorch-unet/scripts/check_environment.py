#!/usr/bin/env python3
"""Check whether a Python environment can use Pytorch-UNet basics.

This root-level helper verifies imports and optional CUDA visibility without
running training, prediction on real files, downloads, or W&B initialization.
Use --repo-root when checking a source checkout that has not been packaged.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from typing import Any, Dict


def emit(payload: Dict[str, Any], code: int = 0) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))
    raise SystemExit(code)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Pytorch-UNet imports and optional CUDA availability")
    parser.add_argument("--repo-root", help="Optional checkout root to add to sys.path before importing unet")
    parser.add_argument("--require-cuda", action="store_true", help="Fail if torch.cuda.is_available() is false")
    parser.add_argument("--skip-wandb", action="store_true", help="Do not import wandb; useful for minimal inference-only checks")
    return parser.parse_args()


def import_status(name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(name)
        return {"ok": True, "version": getattr(module, "__version__", None)}
    except Exception as exc:
        return {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}


def main() -> None:
    args = parse_args()
    if args.repo_root:
        repo_root = os.path.abspath(args.repo_root)
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)
    cwd = os.getcwd()
    if cwd and cwd not in sys.path:
        sys.path.insert(0, cwd)

    modules = ["torch", "torchvision", "PIL", "numpy", "matplotlib", "tqdm", "unet", "utils.data_loading", "utils.dice_score"]
    if not args.skip_wandb:
        modules.append("wandb")
    results = {name: import_status(name) for name in modules}

    cuda = {"available": False, "device_count": 0}
    if results.get("torch", {}).get("ok"):
        import torch

        cuda = {
            "available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()),
            "runtime": getattr(torch.version, "cuda", None),
        }
        if torch.cuda.is_available():
            cuda["device0"] = torch.cuda.get_device_name(0)
            cuda["capability0"] = list(torch.cuda.get_device_capability(0))
            try:
                torch.empty((1,), device="cuda")
                cuda["allocation"] = "passed"
            except Exception as exc:
                cuda["allocation"] = f"failed: {type(exc).__name__}: {exc}"

    errors = {k: v for k, v in results.items() if not v.get("ok")}
    if args.require_cuda and not cuda.get("available"):
        errors["cuda"] = {"ok": False, "error": "CUDA required but torch.cuda.is_available() is false"}

    emit({"ok": not errors, "imports": results, "cuda": cuda, "errors": errors}, 0 if not errors else 1)


if __name__ == "__main__":
    main()
