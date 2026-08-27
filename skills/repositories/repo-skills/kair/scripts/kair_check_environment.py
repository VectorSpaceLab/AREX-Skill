#!/usr/bin/env python3
"""Check a Python environment for KAIR workflows.

This self-contained helper checks dependency imports, PyTorch CUDA availability,
and optionally KAIR checkout import quirks. It does not download models, create
data, or run inference/training.
"""
from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

REQUIRED_IMPORTS = ["cv2", "PIL", "torch", "torchvision", "numpy", "requests"]
SCOPE_IMPORTS = ["skimage", "hdf5storage", "lmdb", "timm", "einops", "ninja"]


def try_import(name: str) -> Tuple[bool, str]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"
    version = getattr(module, "__version__", "unknown-version")
    return True, str(version)


def check_imports(names: Iterable[str]) -> int:
    failures = 0
    for name in names:
        ok, detail = try_import(name)
        status = "OK" if ok else "FAIL"
        print(f"{status}: import {name}: {detail}")
        failures += 0 if ok else 1
    return failures


def check_torch_cuda(require_cuda: bool) -> int:
    ok, detail = try_import("torch")
    if not ok:
        print(f"FAIL: torch import required before CUDA check: {detail}")
        return 1
    import torch  # type: ignore

    print(f"INFO: torch version: {torch.__version__}")
    print(f"INFO: torch CUDA runtime: {torch.version.cuda}")
    available = torch.cuda.is_available()
    print(f"INFO: torch.cuda.is_available: {available}")
    if available:
        print(f"INFO: CUDA device count: {torch.cuda.device_count()}")
        try:
            print(f"INFO: CUDA device 0: {torch.cuda.get_device_name(0)} capability {torch.cuda.get_device_capability(0)}")
            torch.empty((1,), device="cuda")
            print("OK: CUDA tiny tensor allocation succeeded")
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL: CUDA tiny tensor allocation failed: {type(exc).__name__}: {exc}")
            return 1
    elif require_cuda:
        print("FAIL: CUDA was required but torch.cuda.is_available() is false")
        return 1
    else:
        print("WARN: CUDA is unavailable; image-only parser/help checks may still work, but VRT/RVRT/face/custom-op workflows are not fully verified.")
    return 0


def check_kair_root(root: Path, custom_ops: bool) -> int:
    failures = 0
    if not root.exists():
        print(f"FAIL: KAIR root does not exist: {root}")
        return 1
    for rel in ["main_test_swinir.py", "main_test_vrt.py", "models", "data", "utils", "requirement.txt"]:
        path = root / rel
        if path.exists():
            print(f"OK: found {rel}")
        else:
            print(f"WARN: missing expected KAIR path {rel}")
    sys.path.insert(0, str(root))
    if custom_ops:
        sys.path.insert(0, str(root / "models"))
    for name in ["data.select_dataset", "models.select_model", "utils.utils_option"]:
        ok, detail = try_import(name)
        print(("OK" if ok else "FAIL") + f": import {name}: {detail}")
        failures += 0 if ok else 1
    if custom_ops:
        for name in ["models.network_rvrt", "models.network_faceenhancer"]:
            ok, detail = try_import(name)
            print(("OK" if ok else "FAIL") + f": import {name}: {detail}")
            failures += 0 if ok else 1
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Check dependency and optional KAIR checkout readiness.")
    parser.add_argument("--kair-root", type=Path, help="Optional path to a KAIR checkout for source import checks.")
    parser.add_argument("--require-cuda", action="store_true", help="Return nonzero if CUDA is unavailable.")
    parser.add_argument("--check-custom-ops", action="store_true", help="Try imports that may JIT-build CUDA extensions; requires --kair-root and a CUDA toolchain.")
    args = parser.parse_args()

    failures = 0
    print("## Required imports")
    failures += check_imports(REQUIRED_IMPORTS)
    print("\n## Scope imports")
    failures += check_imports(SCOPE_IMPORTS)
    print("\n## PyTorch CUDA")
    failures += check_torch_cuda(args.require_cuda)
    if args.kair_root:
        print("\n## KAIR source import checks")
        failures += check_kair_root(args.kair_root, args.check_custom_ops)
    elif args.check_custom_ops:
        print("FAIL: --check-custom-ops requires --kair-root")
        failures += 1
    print("\nResult: " + ("OK" if failures == 0 else f"{failures} failure(s)"))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
