#!/usr/bin/env python3
"""Check a pytorch-CycleGAN-and-pix2pix runtime environment.

The script can run in any working directory. Pass --repo-root when the target
checkout is not the current directory. It performs import/version/backend checks
only; it does not download data, load checkpoints, train models, or write output
except for normal console text.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

DEPENDENCY_IMPORTS: Tuple[str, ...] = ("torch", "torchvision", "numpy", "PIL", "skimage", "dominate", "wandb")
REPO_IMPORTS: Tuple[str, ...] = ("data", "models", "options", "util", "util.get_data")


def import_one(name: str) -> tuple[bool, str]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        return False, f"{name}: FAIL ({type(exc).__name__}: {exc})"
    version = getattr(module, "__version__", None)
    suffix = f" version={version}" if version else ""
    return True, f"{name}: ok{suffix}"


def check_imports(names: Iterable[str]) -> int:
    failures = 0
    for name in names:
        ok, message = import_one(name)
        print(message)
        failures += 0 if ok else 1
    return failures


def torch_backend() -> int:
    try:
        import torch
    except Exception:
        return 1
    print(f"torch.cuda.is_available: {torch.cuda.is_available()}")
    print(f"torch.cuda.device_count: {torch.cuda.device_count()}")
    if torch.cuda.is_available():
        try:
            device = torch.device("cuda:0")
            sample = torch.empty((1,), device=device)
            print(f"cuda smoke: ok on {torch.cuda.get_device_name(0)} capability={torch.cuda.get_device_capability(0)} shape={tuple(sample.shape)}")
        except Exception as exc:
            print(f"cuda smoke: FAIL ({type(exc).__name__}: {exc})")
            return 1
    return 0


def repo_smoke() -> int:
    try:
        from models import networks
        import torch
    except Exception as exc:
        print(f"repo smoke import: FAIL ({type(exc).__name__}: {exc})")
        return 1
    try:
        generator = networks.define_G(3, 3, 8, "resnet_6blocks", norm="instance", use_dropout=False)
        x = torch.zeros(1, 3, 32, 32)
        y = generator(x)
        print(f"repo generator cpu smoke: ok output_shape={tuple(y.shape)}")
        return 0
    except Exception as exc:
        print(f"repo generator cpu smoke: FAIL ({type(exc).__name__}: {exc})")
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check dependencies, repo imports, and optional torch CUDA availability.")
    parser.add_argument("--repo-root", type=Path, help="Target checkout root to prepend to sys.path before repository import checks.")
    parser.add_argument("--dependencies-only", action="store_true", help="Skip repository module imports and repo CPU smoke.")
    parser.add_argument("--require-cuda", action="store_true", help="Fail if torch CUDA is not available and a tiny CUDA tensor cannot be allocated.")
    return parser


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.repo_root is not None:
        root = args.repo_root.expanduser().resolve()
        if not root.is_dir():
            print(f"ERROR: --repo-root is not a directory: {root}", file=sys.stderr)
            return 2
        sys.path.insert(0, str(root))

    failures = 0
    print("dependency imports:")
    failures += check_imports(DEPENDENCY_IMPORTS)
    failures += torch_backend()
    if args.require_cuda:
        try:
            import torch
            if not torch.cuda.is_available():
                print("ERROR: --require-cuda was set but torch CUDA is unavailable", file=sys.stderr)
                failures += 1
        except Exception:
            failures += 1

    if not args.dependencies_only:
        print("repository imports:")
        failures += check_imports(REPO_IMPORTS)
        failures += repo_smoke()
    if failures:
        print(f"environment check failed: {failures} problem(s)", file=sys.stderr)
        return 1
    print("environment check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
