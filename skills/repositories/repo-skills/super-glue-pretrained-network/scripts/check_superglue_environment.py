#!/usr/bin/env python3
"""Check a SuperGluePretrainedNetwork runtime environment.

This helper is intentionally read-only: it imports dependencies and modules,
checks expected checkpoint files, and reports optional CUDA visibility. It does
not download models, run training, or modify the repository.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

DEPENDENCIES = ["torch", "cv2", "numpy", "matplotlib"]
REPO_MODULES = ["models.matching", "models.superpoint", "models.superglue", "models.utils"]
WEIGHTS = [
    Path("models/weights/superpoint_v1.pth"),
    Path("models/weights/superglue_indoor.pth"),
    Path("models/weights/superglue_outdoor.pth"),
]
TOP_LEVEL = ["demo_superglue.py", "match_pairs.py"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check imports, weights, scripts, and optional CUDA for SuperGluePretrainedNetwork.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        type=Path,
        help="Path to a SuperGluePretrainedNetwork checkout or source tree.",
    )
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="Fail if PyTorch cannot see CUDA. Use only when the task truly needs GPU acceleration.",
    )
    return parser.parse_args()


def add_repo_root(repo_root: Path) -> Path:
    repo_root = repo_root.expanduser().resolve()
    if not repo_root.is_dir():
        raise SystemExit(f"repo root does not exist or is not a directory: {repo_root}")
    if not (repo_root / "models").is_dir():
        raise SystemExit(f"repo root does not contain models/: {repo_root}")
    root_text = str(repo_root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    return repo_root


def import_and_report(name: str):
    module = importlib.import_module(name)
    version = getattr(module, "__version__", None)
    location = getattr(module, "__file__", None)
    suffix = f" version={version}" if version else ""
    print(f"[ok] import {name}{suffix} ({location})")
    return module


def check_files(repo_root: Path) -> int:
    missing = 0
    for rel in TOP_LEVEL + [w.as_posix() for w in WEIGHTS]:
        path = repo_root / rel
        if path.is_file():
            print(f"[ok] file {rel}")
        else:
            print(f"[missing] file {rel}")
            missing += 1
    return missing


def main() -> int:
    args = parse_args()
    repo_root = add_repo_root(args.repo_root)

    failures = 0
    print("== Dependencies ==")
    imported = {}
    for name in DEPENDENCIES:
        try:
            imported[name] = import_and_report(name)
        except Exception as exc:
            print(f"[fail] import {name}: {exc}")
            failures += 1

    print("\n== Repository modules ==")
    for name in REPO_MODULES:
        try:
            import_and_report(name)
        except Exception as exc:
            print(f"[fail] import {name}: {exc}")
            failures += 1

    print("\n== Required files ==")
    failures += check_files(repo_root)

    print("\n== Backend ==")
    torch = imported.get("torch")
    if torch is None:
        print("[fail] torch unavailable, cannot check backend")
        failures += 1
    else:
        cuda_available = bool(torch.cuda.is_available())
        print(f"[info] torch.cuda.is_available={cuda_available}")
        if cuda_available:
            print(f"[info] cuda_device_count={torch.cuda.device_count()}")
            try:
                print(f"[info] cuda_device_0={torch.cuda.get_device_name(0)}")
            except Exception as exc:
                print(f"[warn] could not query device name: {exc}")
        elif args.require_cuda:
            print("[fail] --require-cuda was set but CUDA is unavailable")
            failures += 1

    if failures:
        print(f"\n[fail] {failures} problem(s) found")
        return 1
    print("\n[ok] SuperGluePretrainedNetwork environment looks usable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
