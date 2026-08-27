#!/usr/bin/env python3
"""Check external dependencies and backends for ACT++ workflows.

This diagnostic is safe: it imports packages, reports versions/backends, and
optionally fails if CUDA is unavailable. It does not run MuJoCo episodes,
training, downloads, robot hardware code, or repository scripts.

Example:
    python scripts/check_environment.py --require-cuda
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import os
import sys
from typing import Iterable


def version(dist: str) -> str:
    try:
        return metadata.version(dist)
    except Exception:
        return "unknown"


def check_import(module: str, dist: str | None = None) -> tuple[bool, str]:
    try:
        importlib.import_module(module)
        return True, version(dist or module.split(".")[0])
    except Exception as exc:  # pragma: no cover - diagnostic surface
        return False, f"{type(exc).__name__}: {exc}"


def print_imports(modules: Iterable[tuple[str, str | None]]) -> bool:
    ok = True
    for module, dist in modules:
        passed, detail = check_import(module, dist)
        marker = "OK" if passed else "FAIL"
        print(f"{marker:4} {module:35} {detail}")
        ok = ok and passed
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Check ACT++ external dependency and backend readiness.")
    parser.add_argument("--require-cuda", action="store_true", help="Return non-zero if torch CUDA is unavailable.")
    parser.add_argument("--skip-mujoco", action="store_true", help="Skip DM Control / MuJoCo import checks.")
    args = parser.parse_args()

    modules = [
        ("numpy", "numpy"),
        ("h5py", "h5py"),
        ("cv2", "opencv-python"),
        ("matplotlib", "matplotlib"),
        ("torch", "torch"),
        ("torchvision", "torchvision"),
        ("einops", "einops"),
        ("pyquaternion", "pyquaternion"),
        ("wandb", "wandb"),
        ("diffusers", "diffusers"),
        ("robomimic", "robomimic"),
    ]
    if not args.skip_mujoco:
        modules.extend([
            ("mujoco", "mujoco"),
            ("dm_control.mujoco", "dm_control"),
            ("dm_control.rl.control", "dm_control"),
            ("dm_control.suite.base", "dm_control"),
        ])

    print("ACT++ external dependency check")
    print(f"Python: {sys.version.split()[0]}")
    print(f"MUJOCO_GL: {os.environ.get('MUJOCO_GL', '<unset>')}")
    imports_ok = print_imports(modules)

    cuda_ok = True
    try:
        import torch

        cuda_ok = bool(torch.cuda.is_available())
        print(f"CUDA available: {cuda_ok}")
        if cuda_ok:
            print(f"CUDA device count: {torch.cuda.device_count()}")
            x = torch.ones(1, device="cuda")
            print(f"CUDA allocation smoke: {float(x.item())}")
    except Exception as exc:  # pragma: no cover - diagnostic surface
        cuda_ok = False
        print(f"CUDA check failed: {type(exc).__name__}: {exc}")

    if args.require_cuda and not cuda_ok:
        print("ERROR: CUDA is required for ACT++ training/eval/VINN workflows in the unmodified repo code.")
        return 2
    if not imports_ok:
        print("ERROR: one or more required imports failed.")
        return 1
    print("Environment check finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
