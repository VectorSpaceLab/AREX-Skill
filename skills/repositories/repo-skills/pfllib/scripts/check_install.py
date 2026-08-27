#!/usr/bin/env python3
"""Check the PFLlib runtime stack and optional repo imports.

This helper is safe to run from any directory. It verifies the core Python
packages used by PFLlib, confirms CUDA availability when present, and can also
inspect a checkout by adding `system/` and `dataset/` to `sys.path`.

Example:
  python check_install.py --repo-root /path/to/PFLlib
"""
from __future__ import annotations

import argparse
import sys
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def try_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "missing"
    except Exception as exc:  # pragma: no cover - surfaced to the user
        return f"error: {exc}"


def try_import(label: str, module: str) -> tuple[bool, str]:
    try:
        imported = import_module(module)
        return True, getattr(imported, "__file__", module)
    except Exception as exc:  # pragma: no cover - surfaced to the user
        return False, f"{type(exc).__name__}: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", help="Optional path to a PFLlib checkout for source-level import checks.")
    args = parser.parse_args()

    print(f"python: {sys.executable}")
    print(f"version: {sys.version.split()[0]}")

    core_packages = [
        "torch",
        "torchvision",
        "torchtext",
        "numpy",
        "pandas",
        "scipy",
        "scikit-learn",
        "ujson",
        "h5py",
        "matplotlib",
        "Pillow",
        "cvxpy",
        "calmsize",
    ]
    missing_core = []
    for name in core_packages:
        value = try_version(name)
        print(f"{name}: {value}")
        if value.startswith("missing") or value.startswith("error:"):
            missing_core.append(name)

    try:
        import torch
        cuda_available = torch.cuda.is_available()
        print(f"cuda_available: {cuda_available}")
        print(f"cuda_device_count: {torch.cuda.device_count()}")
        if cuda_available:
            x = torch.tensor([1.0], device="cuda")
            print(f"cuda_smoke: {(x + 1).item()}")
    except Exception as exc:  # pragma: no cover - surfaced to the user
        print(f"cuda_error: {type(exc).__name__}: {exc}")
        return 1

    if args.repo_root:
        repo_root = Path(args.repo_root).expanduser().resolve()
        system_dir = repo_root / "system"
        dataset_dir = repo_root / "dataset"
        if not system_dir.is_dir() or not dataset_dir.is_dir():
            print(f"error: expected system/ and dataset/ under {repo_root}", file=sys.stderr)
            return 2
        sys.path.insert(0, str(system_dir))
        sys.path.insert(0, str(dataset_dir))
        source_modules = [
            ("main", "main"),
            ("serveravg", "flcore.servers.serveravg"),
            ("serverpac", "flcore.servers.serverpac"),
            ("generate_MNIST", "generate_MNIST"),
            ("generate_AGNews", "generate_AGNews"),
            ("generate_HAR", "generate_HAR"),
        ]
        for label, module in source_modules:
            ok, value = try_import(label, module)
            prefix = "ok" if ok else "missing optional dependency"
            print(f"repo_import[{label}]: {prefix} -> {value}")
            if not ok:
                return 1

    if missing_core:
        print(f"missing_core_packages: {', '.join(missing_core)}")
        return 1

    print("install_check: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
