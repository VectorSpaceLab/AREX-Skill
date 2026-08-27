#!/usr/bin/env python3
"""Check a GFPGAN runtime environment without downloading model weights.

Example:
    python scripts/check_env.py --json
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from importlib import metadata
from typing import Any, Dict


def import_status(name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(name)
        version = getattr(module, "__version__", None)
        if version is None:
            try:
                version = metadata.version(name)
            except Exception:
                version = None
        return {"ok": True, "version": version}
    except Exception as exc:  # pragma: no cover - diagnostic output
        return {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate GFPGAN imports, signatures, and optional backend visibility.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    packages = ["gfpgan", "torch", "torchvision", "basicsr", "facexlib", "cv2", "lmdb", "yaml"]
    result: Dict[str, Any] = {"packages": {name: import_status(name) for name in packages}}

    try:
        import torch

        result["torch"] = {
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_version": getattr(torch.version, "cuda", None),
            "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
    except Exception as exc:
        result["torch"] = {"error": f"{exc.__class__.__name__}: {exc}"}

    try:
        from gfpgan.utils import GFPGANer

        result["signatures"] = {
            "GFPGANer.__init__": str(inspect.signature(GFPGANer.__init__)),
            "GFPGANer.enhance": str(inspect.signature(GFPGANer.enhance)),
        }
    except Exception as exc:
        result["signatures"] = {"error": f"{exc.__class__.__name__}: {exc}"}

    try:
        importlib.import_module("realesrgan")
        result["optional"] = {"realesrgan": {"ok": True}}
    except Exception as exc:
        result["optional"] = {"realesrgan": {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}}

    ok = all(status.get("ok") for status in result["packages"].values()) and "error" not in result["signatures"]

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for name, status in result["packages"].items():
            marker = "OK" if status.get("ok") else "FAIL"
            detail = status.get("version") or status.get("error") or ""
            print(f"{marker:4} {name:12} {detail}")
        print("CUDA:", result.get("torch", {}))
        print("Signatures:", result.get("signatures", {}))
        print("Optional:", result.get("optional", {}))

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
