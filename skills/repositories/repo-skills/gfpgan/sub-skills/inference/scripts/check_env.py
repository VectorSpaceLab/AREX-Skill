#!/usr/bin/env python3
"""Check GFPGAN inference imports and signatures without loading weights.

Example:
    python scripts/check_env.py --json
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from typing import Any, Dict


def check() -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    try:
        import torch

        result["torch"] = {
            "ok": True,
            "version": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_version": getattr(torch.version, "cuda", None),
        }
    except Exception as exc:
        result["torch"] = {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}

    for name in ["gfpgan", "cv2", "basicsr", "facexlib"]:
        try:
            module = importlib.import_module(name)
            result[name] = {"ok": True, "version": getattr(module, "__version__", None)}
        except Exception as exc:
            result[name] = {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}

    try:
        from gfpgan import GFPGANer

        result["GFPGANer"] = {
            "ok": True,
            "init": str(inspect.signature(GFPGANer.__init__)),
            "enhance": str(inspect.signature(GFPGANer.enhance)),
        }
    except Exception as exc:
        result["GFPGANer"] = {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}

    try:
        importlib.import_module("realesrgan")
        result["realesrgan"] = {"ok": True}
    except Exception as exc:
        result["realesrgan"] = {"ok": False, "optional": True, "error": f"{exc.__class__.__name__}: {exc}"}

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check GFPGAN inference dependencies without loading model weights.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    args = parser.parse_args()
    result = check()
    required_ok = all(result.get(name, {}).get("ok") for name in ["torch", "gfpgan", "cv2", "basicsr", "facexlib", "GFPGANer"])
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            marker = "OK" if value.get("ok") else ("OPTIONAL-MISSING" if value.get("optional") else "FAIL")
            print(f"{marker:16} {key}: {value}")
    return 0 if required_ok else 1


if __name__ == "__main__":
    sys.exit(main())
