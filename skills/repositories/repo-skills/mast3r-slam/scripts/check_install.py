#!/usr/bin/env python3
"""Check a MASt3R-SLAM Python environment.

Safe by default: imports packages, prints versions, optionally checks CUDA and
checkpoint filenames. It never downloads checkpoints or datasets.

Examples:
  python check_install.py --check-cuda
  python check_install.py --repo-root /path/to/MASt3R-SLAM --checkpoint-dir checkpoints
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import pathlib
import sys
from typing import Iterable

REQUIRED_DISTS = ["MAST3R-SLAM", "MAST3R", "in3d", "lietorch", "evo"]
CORE_IMPORTS = [
    "torch",
    "mast3r_slam",
    "mast3r_slam_backends",
    "mast3r",
    "in3d",
    "lietorch",
    "evo",
]
CHECKPOINTS = [
    "MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth",
    "MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric_retrieval_trainingfree.pth",
    "MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric_retrieval_codebook.pkl",
]
OPTIONAL_IMPORTS = ["pyrealsense2"]


def add_repo_paths(repo_root: pathlib.Path | None) -> None:
    if not repo_root:
        return
    repo_root = repo_root.resolve()
    for path in [repo_root, repo_root / "thirdparty" / "mast3r", repo_root / "thirdparty" / "in3d"]:
        if path.exists():
            sys.path.insert(0, str(path))


def show_versions(names: Iterable[str]) -> list[str]:
    failures: list[str] = []
    for name in names:
        try:
            print(f"dist {name}: {metadata.version(name)}")
        except metadata.PackageNotFoundError:
            failures.append(f"missing distribution metadata: {name}")
    return failures


def import_core() -> list[str]:
    failures: list[str] = []
    for module in CORE_IMPORTS:
        try:
            imported = importlib.import_module(module)
            print(f"import {module}: ok ({getattr(imported, '__file__', 'built-in')})")
        except Exception as exc:  # noqa: BLE001 - diagnostic should report exact import failure
            failures.append(f"import {module}: {type(exc).__name__}: {exc}")

    try:
        importlib.import_module("mast3r.utils.path_to_dust3r")
        dust3r = importlib.import_module("dust3r")
        print(f"import dust3r after mast3r path hook: ok ({getattr(dust3r, '__file__', 'built-in')})")
    except Exception as exc:  # noqa: BLE001
        failures.append(f"import dust3r after mast3r path hook: {type(exc).__name__}: {exc}")
    return failures


def import_optional() -> None:
    for module in OPTIONAL_IMPORTS:
        try:
            imported = importlib.import_module(module)
            print(f"optional import {module}: ok ({getattr(imported, '__file__', 'built-in')})")
        except Exception as exc:  # noqa: BLE001
            print(f"optional import {module}: missing ({type(exc).__name__}: {exc})")


def check_cuda(required: bool) -> list[str]:
    failures: list[str] = []
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        return [f"import torch failed: {type(exc).__name__}: {exc}"]

    print(f"torch: {torch.__version__} cuda={torch.version.cuda}")
    available = torch.cuda.is_available()
    print(f"torch.cuda.is_available: {available}; device_count={torch.cuda.device_count()}")
    if available:
        name = torch.cuda.get_device_name(0)
        cap = torch.cuda.get_device_capability(0)
        torch.empty((1,), device="cuda")
        print(f"cuda smoke: ok ({name}, capability {cap[0]}.{cap[1]})")
    elif required:
        failures.append("CUDA required but torch.cuda.is_available() is false")
    return failures


def check_checkpoints(path: pathlib.Path) -> list[str]:
    failures: list[str] = []
    print(f"checkpoint_dir: {path}")
    for filename in CHECKPOINTS:
        candidate = path / filename
        if candidate.exists():
            size = candidate.stat().st_size
            print(f"checkpoint {filename}: ok ({size} bytes)")
        else:
            failures.append(f"missing checkpoint: {candidate}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Check MASt3R-SLAM imports, CUDA, and checkpoint assets.")
    parser.add_argument("--repo-root", type=pathlib.Path, help="Optional MASt3R-SLAM checkout to add to sys.path before imports.")
    parser.add_argument("--check-cuda", action="store_true", help="Require a passing torch CUDA smoke check.")
    parser.add_argument("--checkpoint-dir", type=pathlib.Path, help="Directory containing the three MASt3R checkpoint assets.")
    args = parser.parse_args()

    add_repo_paths(args.repo_root)
    failures: list[str] = []
    failures.extend(show_versions(REQUIRED_DISTS))
    failures.extend(import_core())
    import_optional()
    failures.extend(check_cuda(required=args.check_cuda))
    if args.checkpoint_dir:
        failures.extend(check_checkpoints(args.checkpoint_dir))

    if failures:
        print("\nFAILED:", file=sys.stderr)
        for item in failures:
            print(f"- {item}", file=sys.stderr)
        return 1
    print("\nMASt3R-SLAM environment checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
