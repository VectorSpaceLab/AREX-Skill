#!/usr/bin/env python3
"""Check a 3D Gaussian Splatting Python environment without running training.

This helper is bundled with the DisCo repo skill. It performs safe import and
backend probes only: no downloads, no dataset reads, no training, and no writes
except normal stdout/stderr. Use --repo-root when checking an editable checkout.
"""

from __future__ import annotations

import argparse
import importlib
import shutil
import sys
from pathlib import Path


def status(level: str, message: str) -> None:
    print(f"[{level}] {message}")


def try_import(name: str):
    try:
        module = importlib.import_module(name)
        status("PASS", f"import {name}")
        return module
    except Exception as exc:  # pragma: no cover - diagnostic surface
        status("FAIL", f"import {name}: {type(exc).__name__}: {exc}")
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safe gaussian-splatting environment preflight")
    parser.add_argument("--repo-root", type=Path, help="Optional checkout containing train.py, scene/, utils/, and gaussian_renderer/.")
    parser.add_argument("--require-cuda", action="store_true", help="Return non-zero if torch CUDA is unavailable.")
    parser.add_argument("--require-extensions", action="store_true", help="Return non-zero if custom CUDA extensions do not import.")
    parser.add_argument("--check-tools", action="store_true", help="Also report optional external tools: colmap, magick, cmake, nvcc.")
    args = parser.parse_args(argv)

    failed = False
    if args.repo_root:
        root = args.repo_root.resolve()
        if not (root / "train.py").is_file():
            status("FAIL", f"--repo-root does not look like a gaussian-splatting checkout: missing train.py under {root}")
            return 2
        sys.path.insert(0, str(root))
        status("INFO", "added --repo-root to sys.path for import checks")

    torch = try_import("torch")
    if torch is None:
        return 2
    status("INFO", f"torch version: {getattr(torch, '__version__', 'unknown')}; torch.version.cuda={getattr(torch.version, 'cuda', None)}")
    cuda_ok = bool(torch.cuda.is_available())
    if cuda_ok:
        try:
            status("PASS", f"CUDA available: {torch.cuda.device_count()} device(s); first={torch.cuda.get_device_name(0)} capability={torch.cuda.get_device_capability(0)}")
            torch.empty((1,), device="cuda")
            status("PASS", "tiny CUDA tensor allocation")
        except Exception as exc:  # pragma: no cover - diagnostic surface
            status("FAIL", f"CUDA allocation failed: {type(exc).__name__}: {exc}")
            failed = True
    else:
        level = "FAIL" if args.require_cuda else "WARN"
        status(level, "torch.cuda.is_available() is false; training/rendering/metrics cannot be truthfully verified")
        failed = failed or args.require_cuda

    for module in ["diff_gaussian_rasterization", "simple_knn._C", "fused_ssim"]:
        ok = try_import(module) is not None
        failed = failed or (args.require_extensions and not ok)

    for module in ["arguments", "scene", "scene.gaussian_model", "gaussian_renderer"]:
        try_import(module)

    if args.check_tools:
        for tool in ["colmap", "magick", "cmake", "nvcc", "g++"]:
            found = shutil.which(tool)
            status("PASS" if found else "WARN", f"tool {tool}: {found or 'not found on PATH'}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
