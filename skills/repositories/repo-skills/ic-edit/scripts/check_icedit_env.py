#!/usr/bin/env python3
"""Cross-cutting environment checker for the ICEdit skill.

Use this helper after installing the bundled package stack to confirm that the
CUDA-enabled editing, demo, and training surfaces are importable.

Examples:
  python scripts/check_icedit_env.py
  python scripts/check_icedit_env.py --repo-root /path/to/ICEdit --check-vendored
  python scripts/check_icedit_env.py --allow-cpu
"""

from __future__ import annotations

import argparse
import sys
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Iterable

REQUIRED_PACKAGES = [
    "diffusers",
    "transformers",
    "gradio",
    "spaces",
    "torch",
    "torchvision",
    "peft",
    "accelerate",
    "gguf",
    "lightning",
    "datasets",
    "opencv-python",
    "prodigyopt",
    "wandb",
]

REQUIRED_IMPORTS = [
    "torch",
    "diffusers",
    "transformers",
    "gradio",
    "lightning",
    "datasets",
    "prodigyopt",
    "wandb",
    "spaces",
    "torchvision",
    "peft",
    "accelerate",
    "gguf",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the ICEdit runtime environment.")
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Optional ICEdit checkout root. When supplied with --check-vendored, the helper also checks the repo-local icedit/ package path.",
    )
    parser.add_argument(
        "--check-vendored",
        action="store_true",
        help="Check that the vendored icedit/ package tree can be imported when present.",
    )
    parser.add_argument(
        "--allow-cpu",
        action="store_true",
        help="Do not fail when CUDA is unavailable. The primary ICEdit workflows still require CUDA.",
    )
    return parser.parse_args()


def print_header(title: str) -> None:
    print(f"\n== {title} ==")


def check_package_metadata(packages: Iterable[str]) -> list[str]:
    missing = []
    print_header("Package metadata")
    for pkg in packages:
        try:
            print(f"{pkg}: {version(pkg)}")
        except PackageNotFoundError:
            print(f"{pkg}: MISSING")
            missing.append(pkg)
    return missing


def check_imports(modules: Iterable[str]) -> list[str]:
    missing = []
    print_header("Imports")
    for mod in modules:
        try:
            module = import_module(mod)
            module_file = getattr(module, "__file__", "<namespace>")
            module_version = getattr(module, "__version__", None)
            if module_version is None:
                print(f"{mod}: ok ({module_file})")
            else:
                print(f"{mod}: ok {module_version} ({module_file})")
        except Exception as exc:  # pragma: no cover - diagnostic path
            print(f"{mod}: MISSING ({exc})")
            missing.append(mod)
    return missing


def check_cuda(allow_cpu: bool) -> bool:
    print_header("CUDA")
    try:
        import torch
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"torch import failed: {exc}")
        return False

    print(f"torch.__version__: {torch.__version__}")
    print(f"torch.version.cuda: {torch.version.cuda}")
    print(f"torch.cuda.is_available(): {torch.cuda.is_available()}")

    if not torch.cuda.is_available():
        if allow_cpu:
            print("CUDA is unavailable, but --allow-cpu was supplied.")
            return True
        print("CUDA is unavailable. Install a CUDA-enabled torch wheel before using ICEdit's primary workflows.")
        return False

    try:
        probe = torch.tensor([1.0], device="cuda")
        print(f"CUDA tensor probe: {probe.device} -> {float(probe.sum().item())}")
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"CUDA tensor probe failed: {exc}")
        return False

    return True


def check_vendored(repo_root: str | None) -> bool:
    if not repo_root:
        print_header("Vendored icedit/")
        print("Skipped because --repo-root was not provided.")
        return True

    root = Path(repo_root).expanduser().resolve()
    vendored = root / "icedit"
    print_header("Vendored icedit/")
    print(f"repo_root: {root}")
    print(f"vendored_path: {vendored}")
    if not vendored.is_dir():
        print("Vendored package tree missing.")
        return False

    if str(vendored) not in sys.path:
        sys.path.insert(0, str(vendored))

    for module_name in list(sys.modules):
        if module_name == "diffusers" or module_name.startswith("diffusers."):
            sys.modules.pop(module_name, None)

    try:
        import diffusers as local_diffusers
        print(f"vendored diffusers: {local_diffusers.__version__} ({local_diffusers.__file__})")
        return True
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"Vendored diffusers import failed: {exc}")
        return False


def main() -> int:
    args = parse_args()

    metadata_missing = check_package_metadata(REQUIRED_PACKAGES)
    import_missing = check_imports(REQUIRED_IMPORTS)
    cuda_ok = check_cuda(args.allow_cpu)
    vendored_ok = check_vendored(args.repo_root) if args.check_vendored else True

    print_header("Summary")
    print(f"package_metadata_missing: {metadata_missing}")
    print(f"import_missing: {import_missing}")
    print(f"cuda_ok: {cuda_ok}")
    print(f"vendored_ok: {vendored_ok}")

    if metadata_missing or import_missing or not cuda_ok or not vendored_ok:
        return 1

    print("ICEdit environment check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
