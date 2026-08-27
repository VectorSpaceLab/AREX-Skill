#!/usr/bin/env python3
"""Check whether the active Python environment can import Diffusers pipeline basics."""

from __future__ import annotations

import argparse
import importlib
import platform
import sys


def import_status(module_name: str) -> tuple[bool, str]:
    try:
        module = importlib.import_module(module_name)
    except Exception as error:  # noqa: BLE001 - report import diagnostics without hiding type
        return False, f"{type(error).__name__}: {error}"
    version = getattr(module, "__version__", "unknown")
    return True, str(version)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Diffusers pipeline imports, torch backend availability, and common optional dependencies."
    )
    parser.add_argument(
        "--optional",
        nargs="*",
        default=["transformers", "accelerate", "safetensors", "PIL"],
        help="Optional dependency module names to check. Defaults to common pipeline dependencies.",
    )
    parser.add_argument(
        "--require-optional",
        action="store_true",
        help="Exit nonzero if any optional dependency listed by --optional is missing.",
    )
    args = parser.parse_args()

    print(f"python: {sys.version.split()[0]}")
    print(f"platform: {platform.platform()}")

    diffusers_ok, diffusers_info = import_status("diffusers")
    print(f"diffusers: {'ok' if diffusers_ok else 'missing'} ({diffusers_info})")
    if not diffusers_ok:
        return 2

    try:
        from diffusers import AutoPipelineForText2Image, DiffusionPipeline

        print(f"DiffusionPipeline: ok ({DiffusionPipeline.__name__})")
        print(f"AutoPipelineForText2Image: ok ({AutoPipelineForText2Image.__name__})")
    except Exception as error:  # noqa: BLE001
        print(f"pipeline imports: failed ({type(error).__name__}: {error})")
        return 3

    torch_ok, torch_info = import_status("torch")
    print(f"torch: {'ok' if torch_ok else 'missing'} ({torch_info})")
    if torch_ok:
        import torch

        print(f"cuda_available: {torch.cuda.is_available()}")
        mps_available = bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available())
        print(f"mps_available: {mps_available}")
        recommended_device = "cuda" if torch.cuda.is_available() else "mps" if mps_available else "cpu"
        recommended_dtype = "torch.float16" if recommended_device == "cuda" else "torch.float32"
        print(f"recommended_default: device={recommended_device} dtype={recommended_dtype}")

    missing_optional: list[str] = []
    for module_name in args.optional:
        ok, info = import_status(module_name)
        print(f"optional {module_name}: {'ok' if ok else 'missing'} ({info})")
        if not ok:
            missing_optional.append(module_name)

    if args.require_optional and missing_optional:
        print("missing required optional dependencies: " + ", ".join(missing_optional))
        return 4

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
