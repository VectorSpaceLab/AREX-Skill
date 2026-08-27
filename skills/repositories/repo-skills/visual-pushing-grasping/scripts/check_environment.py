#!/usr/bin/env python3
"""Report the safe Python/backend prerequisites for Visual Pushing and Grasping.

This helper performs imports and a tiny optional CUDA allocation only. It does
not import the repository, download weights, connect to a simulator/camera, or
move a robot. Run it from any working directory.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check VPG numerical and optional CUDA prerequisites safely.")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--require-cuda", action="store_true", help="return nonzero unless a CUDA tensor allocation succeeds")
    return parser


def check(require_cuda: bool = False) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {"python": sys.version.split()[0], "imports": {}, "cuda": {"available": False}}
    code = 0
    for name in ("numpy", "scipy", "cv2", "matplotlib", "torch", "torchvision"):
        try:
            module = importlib.import_module(name)
            result["imports"][name] = getattr(module, "__version__", "ok")
        except Exception as exc:  # report every missing optional/runtime dependency together
            result["imports"][name] = {"error": f"{type(exc).__name__}: {exc}"}
            code = 2
    try:
        import torch

        result["cuda"] = {
            "available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()),
            "torch_cuda_build": torch.version.cuda,
        }
        if torch.cuda.is_available():
            result["cuda"]["device"] = torch.cuda.get_device_name(0)
            result["cuda"]["capability"] = list(torch.cuda.get_device_capability(0))
            torch.empty((1,), device="cuda")
            result["cuda"]["allocation"] = "passed"
        elif require_cuda:
            result["cuda"]["allocation"] = "blocked"
            code = max(code, 3)
    except Exception as exc:
        result["cuda"]["error"] = f"{type(exc).__name__}: {exc}"
        if require_cuda:
            code = max(code, 3)
    return result, code


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result, code = check(args.require_cuda)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Python: {result['python']}")
        for name, version in result["imports"].items():
            print(f"{name}: {version}")
        print(f"CUDA: {result['cuda']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
