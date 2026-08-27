#!/usr/bin/env python3
"""Safe OpenRLHF runtime diagnostic.

This script avoids importing OpenRLHF internals, starting Ray, loading models,
running DeepSpeed, or requiring GPUs. It reports package visibility, selected
environment variables, and torch CUDA status if torch is already importable.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import os
import platform
import sys
from typing import Any


PACKAGE_IMPORTS = {
    "openrlhf": "openrlhf",
    "torch": "torch",
    "deepspeed": "deepspeed",
    "ray": "ray",
    "vllm": "vllm",
    "flash-attn": "flash_attn",
    "ring_flash_attn": "ring_flash_attn",
    "liger_kernel": "liger_kernel",
    "peft": "peft",
    "transformers": "transformers",
    "datasets": "datasets",
    "bitsandbytes": "bitsandbytes",
    "wandb": "wandb",
    "pynvml": "pynvml",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
}

DISTRIBUTIONS = {
    "openrlhf": "openrlhf",
    "torch": "torch",
    "deepspeed": "deepspeed",
    "ray": "ray",
    "vllm": "vllm",
    "flash-attn": "flash-attn",
    "ring_flash_attn": "ring-flash-attn",
    "liger_kernel": "liger-kernel",
    "peft": "peft",
    "transformers": "transformers",
    "datasets": "datasets",
    "bitsandbytes": "bitsandbytes",
    "wandb": "wandb",
    "pynvml": "pynvml",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
}

ENV_VARS = [
    "NCCL_DEBUG",
    "TOKENIZERS_PARALLELISM",
    "RAY_ENABLE_ZERO_COPY_TORCH_TENSORS",
    "RAY_EXPERIMENTAL_NOSET_CUDA_VISIBLE_DEVICES",
    "CUDA_VISIBLE_DEVICES",
    "CUDA_HOME",
    "LD_LIBRARY_PATH",
]


def has_import(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def dist_version(distribution_name: str) -> str | None:
    try:
        return importlib.metadata.version(distribution_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def print_section(title: str) -> None:
    print(f"\n== {title} ==")


def print_kv(key: str, value: Any) -> None:
    print(f"{key}: {value}")


def report_python() -> None:
    print_section("Python")
    print_kv("executable", sys.executable)
    print_kv("version", sys.version.replace("\n", " "))
    print_kv("platform", platform.platform())


def report_env() -> None:
    print_section("Environment")
    for name in ENV_VARS:
        print_kv(name, os.environ.get(name, "<unset>"))


def report_packages() -> None:
    print_section("Package visibility")
    for label, module_name in PACKAGE_IMPORTS.items():
        distribution_name = DISTRIBUTIONS[label]
        available = has_import(module_name)
        version = dist_version(distribution_name)
        print_kv(label, f"importable={available} version={version or '<unknown>'}")


def report_torch_cuda() -> None:
    print_section("Torch CUDA")
    if not has_import("torch"):
        print("torch is not importable; skipping CUDA checks")
        return

    try:
        import torch
    except Exception as exc:  # pragma: no cover - diagnostic path
        print_kv("torch import error", f"{type(exc).__name__}: {exc}")
        return

    print_kv("torch version", getattr(torch, "__version__", "<unknown>"))
    print_kv("torch cuda runtime", getattr(torch.version, "cuda", None))

    try:
        cuda_available = torch.cuda.is_available()
    except Exception as exc:  # pragma: no cover - diagnostic path
        print_kv("torch.cuda.is_available error", f"{type(exc).__name__}: {exc}")
        return

    print_kv("cuda available", cuda_available)

    try:
        print_kv("cuda device count", torch.cuda.device_count())
    except Exception as exc:  # pragma: no cover - diagnostic path
        print_kv("torch.cuda.device_count error", f"{type(exc).__name__}: {exc}")

    if cuda_available:
        try:
            print_kv("current device", torch.cuda.current_device())
            print_kv("device name", torch.cuda.get_device_name(torch.cuda.current_device()))
        except Exception as exc:  # pragma: no cover - diagnostic path
            print_kv("torch.cuda device detail error", f"{type(exc).__name__}: {exc}")


def main() -> int:
    report_python()
    report_env()
    report_packages()
    report_torch_cuda()
    print("\nDiagnostic complete. This is not a full OpenRLHF GPU/runtime readiness proof.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
