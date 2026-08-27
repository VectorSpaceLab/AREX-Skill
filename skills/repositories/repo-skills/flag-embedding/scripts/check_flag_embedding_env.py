#!/usr/bin/env python3
"""Check FlagEmbedding package imports and selected optional dependencies.

This script is safe by default: it does not download models, run evaluation, or
launch training. Optional flags add import-only checks for evaluation,
fine-tuning, and CUDA availability.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Iterable


BASE_SYMBOLS = [
    "FlagAutoModel",
    "FlagAutoReranker",
    "FlagModel",
    "BGEM3FlagModel",
    "FlagReranker",
]


def _status(ok: bool, label: str, detail: str = "") -> None:
    prefix = "OK" if ok else "FAIL"
    message = f"{prefix}: {label}"
    if detail:
        message += f" - {detail}"
    print(message)


def _import_module(name: str) -> bool:
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        _status(False, f"import {name}", f"{type(exc).__name__}: {exc}")
        return False
    version_text = getattr(module, "__version__", None)
    _status(True, f"import {name}", str(version_text) if version_text else "")
    return True


def check_base() -> bool:
    ok = True
    try:
        import FlagEmbedding as flag_embedding
        from FlagEmbedding import FlagAutoModel, FlagAutoReranker
    except Exception as exc:
        _status(False, "import FlagEmbedding", f"{type(exc).__name__}: {exc}")
        return False

    try:
        package_version = version("FlagEmbedding")
    except PackageNotFoundError:
        package_version = "metadata-not-found"
        ok = False
    _status(package_version != "metadata-not-found", "FlagEmbedding metadata", package_version)

    missing = [name for name in BASE_SYMBOLS if not hasattr(flag_embedding, name)]
    if missing:
        _status(False, "public symbols", "missing " + ", ".join(missing))
        ok = False
    else:
        _status(True, "public symbols", ", ".join(BASE_SYMBOLS))

    _status(True, "FlagAutoModel.from_finetuned", str(inspect.signature(FlagAutoModel.from_finetuned)))
    _status(True, "FlagAutoReranker.from_finetuned", str(inspect.signature(FlagAutoReranker.from_finetuned)))
    return ok


def check_modules(names: Iterable[str]) -> bool:
    ok = True
    for name in names:
        ok = _import_module(name) and ok
    return ok


def check_evaluation() -> bool:
    ok = check_modules(["faiss", "pytrec_eval"])
    ok = _import_module("FlagEmbedding.evaluation.custom") and ok
    if ok:
        _status(True, "evaluation imports", "custom evaluation dependencies are importable")
    return ok


def check_finetune() -> bool:
    ok = True
    optional = ["deepspeed", "flash_attn"]
    for name in optional:
        try:
            importlib.import_module(name)
        except Exception as exc:
            _status(False, f"optional fine-tune import {name}", f"{type(exc).__name__}: {exc}")
            ok = False
        else:
            _status(True, f"optional fine-tune import {name}")
    ok = _import_module("FlagEmbedding.finetune.embedder.encoder_only.base") and ok
    ok = _import_module("FlagEmbedding.finetune.reranker.encoder_only.base") and ok
    return ok


def check_cuda() -> bool:
    try:
        import torch
    except Exception as exc:
        _status(False, "import torch", f"{type(exc).__name__}: {exc}")
        return False

    cuda_available = torch.cuda.is_available()
    detail = f"torch={torch.__version__} cuda_runtime={torch.version.cuda} available={cuda_available} devices={torch.cuda.device_count()}"
    if not cuda_available:
        _status(False, "CUDA availability", detail)
        return False

    try:
        device_name = torch.cuda.get_device_name(0)
        capability = torch.cuda.get_device_capability(0)
        torch.empty((1,), device="cuda")
    except Exception as exc:
        _status(False, "CUDA tensor smoke", f"{type(exc).__name__}: {exc}")
        return False
    _status(True, "CUDA tensor smoke", f"{device_name} capability={capability}")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-evaluation", action="store_true", help="Import faiss, pytrec_eval, and custom evaluation module")
    parser.add_argument("--check-finetune", action="store_true", help="Import fine-tuning modules and optional DeepSpeed/flash-attn dependencies")
    parser.add_argument("--check-cuda", action="store_true", help="Run a tiny CUDA tensor smoke check")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ok = check_base()
    if args.check_evaluation:
        ok = check_evaluation() and ok
    if args.check_finetune:
        ok = check_finetune() and ok
    if args.check_cuda:
        ok = check_cuda() and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
