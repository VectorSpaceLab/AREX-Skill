#!/usr/bin/env python3
"""Backend-specific preflight for 3D Gaussian Splatting.

Safe checks only. This script verifies imports, CUDA visibility, extension imports,
and optional external command availability without running train.py/render.py.
"""

from __future__ import annotations

import argparse
import importlib
import shutil
import sys
from pathlib import Path


def line(level: str, text: str) -> None:
    print(f"[{level}] {text}")


def import_ok(name: str) -> bool:
    try:
        importlib.import_module(name)
        line("PASS", f"import {name}")
        return True
    except Exception as exc:
        line("FAIL", f"import {name}: {type(exc).__name__}: {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Check gaussian-splatting CUDA/backend readiness")
    parser.add_argument("--repo-root", type=Path, help="Optional checkout root to add for package imports.")
    parser.add_argument("--require-cuda", action="store_true", help="Fail if CUDA is unavailable.")
    parser.add_argument("--require-extensions", action="store_true", help="Fail if custom CUDA extensions cannot import.")
    parser.add_argument("--tools", action="store_true", help="Report optional tools: colmap, magick, cmake, nvcc, g++.")
    args = parser.parse_args()

    failed = False
    if args.repo_root:
        root = args.repo_root.resolve()
        if not (root / "train.py").exists():
            line("FAIL", "--repo-root must contain train.py")
            return 2
        sys.path.insert(0, str(root))

    if not import_ok("torch"):
        return 2
    import torch
    line("INFO", f"torch={torch.__version__}; torch.version.cuda={torch.version.cuda}")
    if torch.cuda.is_available():
        try:
            line("PASS", f"CUDA devices={torch.cuda.device_count()}; first={torch.cuda.get_device_name(0)}; capability={torch.cuda.get_device_capability(0)}")
            torch.empty((1,), device="cuda")
            line("PASS", "tiny CUDA tensor allocation")
        except Exception as exc:
            line("FAIL", f"CUDA tensor allocation failed: {type(exc).__name__}: {exc}")
            failed = True
    else:
        line("FAIL" if args.require_cuda else "WARN", "CUDA unavailable; core train/render/metrics workflows need CUDA")
        failed = failed or args.require_cuda

    for mod in ["diff_gaussian_rasterization", "simple_knn._C", "fused_ssim"]:
        ok = import_ok(mod)
        failed = failed or (args.require_extensions and not ok)

    for mod in ["arguments", "scene", "gaussian_renderer"]:
        import_ok(mod)

    if args.tools:
        for tool in ["colmap", "magick", "cmake", "nvcc", "g++"]:
            found = shutil.which(tool)
            line("PASS" if found else "WARN", f"{tool}: {found or 'not found'}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
