#!/usr/bin/env python3
"""Check the shared CS230 example dependencies and optional local workflow imports.

This helper is safe and read-only. Use it before a workflow-specific command to
confirm that the mixed PyTorch/TensorFlow environment can import the shared
packages and, when `--repo-root` is provided, the local workflow modules from a
checkout.

Example:
    python scripts/check_env.py --frameworks pytorch tensorflow
    python scripts/check_env.py --repo-root /path/to/cs230-code-examples
"""

from __future__ import annotations

import argparse
import importlib
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Iterable, Sequence


SHARED_MODULES = ("numpy", "PIL", "tabulate", "tqdm")
PYTORCH_LOCAL_PATHS = (
    ("pytorch/vision", ("utils", "model.net", "model.data_loader")),
    ("pytorch/nlp", ("utils", "model.net", "model.data_loader")),
)
TENSORFLOW_LOCAL_PATHS = (
    ("tensorflow/vision", ("model.utils", "model.input_fn", "model.model_fn", "model.training", "model.evaluation")),
    ("tensorflow/nlp", ("model.utils", "model.input_fn", "model.model_fn", "model.training", "model.evaluation")),
)


def import_module(name: str):
    module = importlib.import_module(name)
    version = getattr(module, "__version__", None)
    return module, version


def report_shared_modules() -> bool:
    ok = True
    for module_name in SHARED_MODULES:
        try:
            module, version = import_module(module_name)
            label = module_name if module_name != "PIL" else "Pillow"
            print(f"[ok] {label}: {version or 'imported'}")
        except Exception as exc:  # pragma: no cover - defensive diagnostic path
            ok = False
            print(f"[fail] {module_name}: {exc}")
    return ok


def report_pytorch() -> bool:
    try:
        import torch
        import torchvision
    except Exception as exc:
        print(f"[fail] pytorch stack: {exc}")
        return False

    print(f"[ok] torch: {torch.__version__}")
    print(f"[ok] torchvision: {torchvision.__version__}")
    print(f"[info] torch.cuda.is_available(): {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        try:
            sample = torch.empty((1,), device="cuda")
            print(f"[ok] torch CUDA smoke: {sample.device} / {torch.cuda.get_device_name(0)}")
        except Exception as exc:
            print(f"[fail] torch CUDA smoke: {exc}")
            return False
    return True


def report_tensorflow() -> bool:
    try:
        import tensorflow as tf
    except Exception as exc:
        print(f"[fail] tensorflow stack: {exc}")
        return False

    print(f"[ok] tensorflow: {tf.__version__}")
    print(f"[info] tf.contrib available: {hasattr(tf, 'contrib')}")
    print(f"[info] tf.train.AdamOptimizer available: {hasattr(tf.train, 'AdamOptimizer')}")
    if hasattr(tf, "test"):
        try:
            print(f"[info] tf.test.is_built_with_cuda(): {tf.test.is_built_with_cuda()}")
        except Exception:
            pass
    return True


def probe_local_imports(repo_root: Path, rel_path: str, module_names: Sequence[str]) -> bool:
    abs_path = str((repo_root / rel_path).resolve())
    code = textwrap.dedent(
        f"""
        import importlib
        import sys
        sys.path.insert(0, {abs_path!r})
        for module_name in {list(module_names)!r}:
            importlib.import_module(module_name)
        print('ok')
        """
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", code],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"[ok] {rel_path}: local imports succeeded")
        return True

    stderr = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else ""
    print(f"[fail] {rel_path}: {stderr or 'local imports failed'}")
    return False


def report_local_workflows(repo_root: Path, frameworks: Iterable[str]) -> bool:
    ok = True
    if "pytorch" in frameworks:
        for rel_path, module_names in PYTORCH_LOCAL_PATHS:
            ok &= probe_local_imports(repo_root, rel_path, module_names)
    if "tensorflow" in frameworks:
        for rel_path, module_names in TENSORFLOW_LOCAL_PATHS:
            ok &= probe_local_imports(repo_root, rel_path, module_names)
    return ok


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check shared CS230 example dependencies and local workflow imports.")
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Optional repository root used to probe the local workflow modules.",
    )
    parser.add_argument(
        "--frameworks",
        nargs="+",
        choices=("pytorch", "tensorflow"),
        default=["pytorch", "tensorflow"],
        help="Framework families to check.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    ok = report_shared_modules()

    if "pytorch" in args.frameworks:
        ok &= report_pytorch()
    if "tensorflow" in args.frameworks:
        ok &= report_tensorflow()

    if args.repo_root:
        ok &= report_local_workflows(Path(args.repo_root), args.frameworks)

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
