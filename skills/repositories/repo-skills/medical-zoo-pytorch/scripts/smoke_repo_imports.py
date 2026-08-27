#!/usr/bin/env python3
"""Cross-cutting import smoke for MedicalZooPytorch."""

from __future__ import annotations

import argparse
import importlib
import sys
from contextlib import contextmanager
from pathlib import Path

import torch

TARGET_MODULES = [
    "lib",
    "lib.medzoo",
    "lib.medloaders",
    "lib.losses3D",
    "lib.train",
    "lib.visual3D_temp",
]
OPTIONAL_MODULES = ["nibabel", "torchsummary", "torchsummaryX", "torchvision"]


@contextmanager
def added_sys_path(path: str | None):
    if not path:
        yield
        return
    sys.path.insert(0, path)
    try:
        yield
    finally:
        if sys.path and sys.path[0] == path:
            sys.path.pop(0)


def detect_repo_root() -> str | None:
    here = Path(__file__).resolve()
    for parent in (here.parent, *here.parents):
        if (parent / "lib" / "medzoo" / "__init__.py").is_file():
            return str(parent)
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke the MedicalZooPytorch import surface and optional CUDA availability.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--package-root",
        default=None,
        help="Optional local directory to prepend to sys.path before importing lib.* modules.",
    )
    parser.add_argument(
        "--cuda",
        action="store_true",
        default=False,
        help="Also check CUDA availability and allocate a tiny tensor when CUDA is present.",
    )
    return parser.parse_args()


def import_from_candidates(module_name: str, candidate_roots: list[str | None]):
    last_error: Exception | None = None
    for root in candidate_roots:
        with added_sys_path(root):
            try:
                return importlib.import_module(module_name)
            except Exception as exc:
                last_error = exc
    raise SystemExit(
        f"Unable to import {module_name}. Make the MedicalZooPytorch checkout importable and ensure its optional runtime dependencies are installed."
    ) from last_error


def main() -> None:
    args = parse_args()
    candidate_roots = [args.package_root, detect_repo_root()]

    if args.package_root is not None and not Path(args.package_root).expanduser().exists():
        raise SystemExit(f"package root does not exist: {args.package_root}")

    imported = {}
    for module_name in TARGET_MODULES:
        module = import_from_candidates(module_name, candidate_roots)
        imported[module_name] = module
        module_path = getattr(module, "__file__", None)
        print(f"[ok] imported {module_name}{f' -> {module_path}' if module_path else ''}")

    with added_sys_path(args.package_root or detect_repo_root()):
        from lib.losses3D import create_loss
        from lib.medloaders import generate_datasets
        from lib.medzoo import create_model
        from lib.train import Trainer
        from lib.visual3D_temp import TensorboardWriter

    print(f"[ok] create_model -> {create_model.__module__}.{create_model.__name__}")
    print(f"[ok] generate_datasets -> {generate_datasets.__module__}.{generate_datasets.__name__}")
    print(f"[ok] create_loss -> {create_loss.__module__}.{create_loss.__name__}")
    print(f"[ok] Trainer -> {Trainer.__module__}.{Trainer.__name__}")
    print(f"[ok] TensorboardWriter -> {TensorboardWriter.__module__}.{TensorboardWriter.__name__}")

    for module_name in OPTIONAL_MODULES:
        module = import_from_candidates(module_name, candidate_roots)
        module_path = getattr(module, "__file__", None)
        print(f"[ok] optional import {module_name}{f' -> {module_path}' if module_path else ''}")

    if args.cuda:
        if torch.cuda.is_available():
            device = torch.device("cuda:0")
            tensor = torch.ones(1, device=device)
            props = torch.cuda.get_device_properties(0)
            print(f"[ok] CUDA tensor allocated on {props.name} ({props.major}.{props.minor}) with value {float(tensor.item()):.1f}")
        else:
            print("[warn] --cuda requested, but CUDA is not available; CPU import checks still passed")

    print("[done] MedicalZooPytorch import smoke passed")


if __name__ == "__main__":
    main()
