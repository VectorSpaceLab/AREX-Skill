#!/usr/bin/env python3
"""Check dependencies needed by U-2-Net skill workflows.

This script is a runtime diagnostic for future agents. It does not install
packages, download weights, or require the original repository unless --repo-root
is supplied for local module checks.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Dict

MODULES = ["torch", "torchvision", "numpy", "skimage", "PIL", "cv2", "matplotlib"]


def check_module(name: str) -> Dict[str, Any]:
    try:
        mod = importlib.import_module(name)
        return {"ok": True, "version": getattr(mod, "__version__", None)}
    except Exception as exc:  # pragma: no cover - environment specific
        return {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check U-2-Net runtime dependencies and optional local checkout imports.")
    parser.add_argument("--repo-root", type=Path, default=None, help="Optional local U-2-Net checkout to validate model/data_loader imports.")
    parser.add_argument("--check-cuda", action="store_true", help="Also report torch CUDA availability when torch imports.")
    args = parser.parse_args()

    result: Dict[str, Any] = {"ok": True, "modules": {}, "repo": None}
    for name in MODULES:
        result["modules"][name] = check_module(name)
        if not result["modules"][name]["ok"]:
            result["ok"] = False
    if args.check_cuda and result["modules"].get("torch", {}).get("ok"):
        import torch
        result["cuda"] = {"available": bool(torch.cuda.is_available()), "version": torch.version.cuda, "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0}
    if args.repo_root is not None:
        root = args.repo_root.expanduser().resolve()
        result["repo"] = {"path_supplied": True, "model_import": None, "data_loader_import": None}
        if not (root / "model" / "__init__.py").is_file() or not (root / "data_loader.py").is_file():
            result["repo"]["error"] = "repo root must contain model/__init__.py and data_loader.py"
            result["ok"] = False
        else:
            sys.path.insert(0, str(root))
            for name in ("model", "data_loader"):
                check = check_module(name)
                result["repo"][f"{name}_import"] = check
                if not check["ok"]:
                    result["ok"] = False
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
