#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import sys
from typing import Iterable

DEFAULT_MODULES = [
    "torch",
    "torchvision",
    "diffusers",
    "accelerate",
    "transformers",
    "clip",
    "clip_retrieval",
    "huggingface_hub",
    "pandas",
    "scipy",
    "sklearn",
    "tqdm",
]

def probe_module(name: str) -> dict[str, object]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - runtime probe
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "version": getattr(module, "__version__", None)}

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the runtime import and CUDA stack for Custom Diffusion.")
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="Exit non-zero if torch imports but CUDA is unavailable.",
    )
    parser.add_argument(
        "--modules",
        nargs="*",
        default=DEFAULT_MODULES,
        help="Optional module names to probe instead of the default diffusers stack.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    report: dict[str, object] = {"modules": {name: probe_module(name) for name in args.modules}}
    torch_info = report["modules"].get("torch")
    if isinstance(torch_info, dict) and torch_info.get("ok"):
        try:
            torch = importlib.import_module("torch")
            report["cuda"] = {
                "available": bool(torch.cuda.is_available()),
                "device_count": int(torch.cuda.device_count()),
                "torch_cuda": getattr(torch.version, "cuda", None),
            }
        except Exception as exc:  # pragma: no cover - runtime probe
            report["cuda"] = {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    else:
        report["cuda"] = {"available": False, "error": "torch could not be imported"}

    if args.require_cuda and not report["cuda"].get("available", False):
        print("CUDA is not available in this runtime.", file=sys.stderr)
        return 2

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
