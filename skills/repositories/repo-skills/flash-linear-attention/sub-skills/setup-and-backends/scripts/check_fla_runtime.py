#!/usr/bin/env python3
"""Safe FLA runtime checker.

This helper imports FLA, torch, and triton; prints versions and public export
counts; optionally shows selected FLA environment variables; and optionally
requires a tiny CUDA tensor allocation. It does not download data, train models,
compile FLA kernels, or run native repository tests.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import importlib.util
import os
import platform
import sys
from types import ModuleType
from typing import Any

FLA_ENV_VARS = [
    "FLA_CONV_BACKEND",
    "FLA_TRIL_PRECISION",
    "FLA_USE_FAST_OPS",
    "FLA_USE_TMA",
    "FLA_USE_COMPILE",
    "FLA_DISABLE_BACKEND_DISPATCH",
    "FLA_TILELANG",
    "FLA_FLASH_KDA",
    "FLA_INTRACARD_CP",
    "FLA_INTRACARD_MAX_SPLITS",
    "FLA_CACHE_MODE",
    "FLA_CACHE_RESULTS",
    "FLA_CONFIG_DIR",
    "FLA_GPU_NAME",
    "FLA_DISABLE_TENSOR_CACHE",
    "FLA_CI_ENV",
    "FLA_BENCH_OP_WARMUP_ITERS",
    "FLA_BENCH_WARMUP_MS",
    "FLA_BENCH_REP_MS",
    "FLA_BENCH_COOLDOWN_SEC",
]

OPTIONAL_MODULES = {
    "tilelang": "TileLang optional backend",
    "flash_kda": "FlashKDA optional backend",
    "causal_conv1d": "CUDA short-convolution optional backend",
    "torch_npu": "Ascend NPU PyTorch extension",
    "triton_ascend": "Ascend Triton package marker",
}

DISTRIBUTIONS = [
    "flash-linear-attention",
    "fla-core",
    "torch",
    "triton",
    "transformers",
    "einops",
    "tilelang",
    "flash-kda",
    "causal-conv1d",
    "torch-npu",
    "triton-ascend",
]

EXPORT_MODULES = [
    "fla",
    "fla.ops",
    "fla.layers",
    "fla.models",
    "fla.modules",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check that Flash Linear Attention imports with the selected torch/triton backend.",
    )
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="fail unless torch.cuda is available and a tiny CUDA tensor allocation succeeds",
    )
    parser.add_argument(
        "--show-env-vars",
        action="store_true",
        help="print selected FLA_* environment variables that affect dispatch, precision, cache, and benchmarks",
    )
    return parser.parse_args()


def import_required(name: str, hint: str) -> ModuleType | None:
    try:
        return importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - diagnostics should show the original import failure.
        print(f"ERROR: failed to import {name}: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        print(f"HINT: {hint}", file=sys.stderr)
        return None


def dist_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not installed as a distribution"
    except Exception as exc:  # noqa: BLE001 - metadata backends can fail in broken environments.
        return f"metadata error: {exc.__class__.__name__}: {exc}"


def module_version(module: ModuleType, fallback: str = "unknown") -> str:
    return str(getattr(module, "__version__", fallback))


def find_optional_module(name: str) -> str:
    try:
        spec = importlib.util.find_spec(name)
    except Exception as exc:  # noqa: BLE001 - broken optional packages should not hide required import status.
        return f"error while probing: {exc.__class__.__name__}: {exc}"
    return "present" if spec is not None else "not importable"


def export_count(module_name: str) -> str:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - report optional submodule import failures without masking core imports.
        return f"unavailable: {exc.__class__.__name__}: {exc}"
    exported: Any = getattr(module, "__all__", None)
    if exported is None:
        return "no __all__"
    try:
        return str(len(exported))
    except TypeError:
        return "__all__ has no length"


def print_header() -> None:
    print("== Python and platform ==")
    print(f"python: {sys.version.split()[0]}")
    print(f"executable: {sys.executable}")
    print(f"platform: {platform.platform()}")
    print(f"machine: {platform.machine()}")
    print()


def print_versions(fla: ModuleType, torch: ModuleType, triton: ModuleType) -> None:
    print("== Module versions ==")
    print(f"fla.__version__: {module_version(fla)}")
    print(f"torch.__version__: {module_version(torch)}")
    print(f"triton.__version__: {module_version(triton)}")
    print()

    print("== Distribution versions ==")
    for name in DISTRIBUTIONS:
        print(f"{name}: {dist_version(name)}")
    print()


def print_export_counts() -> None:
    print("== Public export counts ==")
    for module_name in EXPORT_MODULES:
        print(f"{module_name}: {export_count(module_name)}")
    print()


def print_torch_backend(torch: ModuleType, triton: ModuleType) -> None:
    print("== Torch / accelerator summary ==")
    cuda = getattr(torch, "cuda", None)
    torch_version = getattr(torch, "version", None)
    print(f"torch.version.cuda: {getattr(torch_version, 'cuda', None)}")
    print(f"torch.version.hip: {getattr(torch_version, 'hip', None)}")
    if cuda is not None:
        try:
            cuda_available = bool(cuda.is_available())
        except Exception as exc:  # noqa: BLE001
            cuda_available = False
            print(f"torch.cuda.is_available error: {exc.__class__.__name__}: {exc}")
        print(f"torch.cuda.is_available: {cuda_available}")
        try:
            print(f"torch.cuda.device_count: {cuda.device_count()}")
        except Exception as exc:  # noqa: BLE001
            print(f"torch.cuda.device_count error: {exc.__class__.__name__}: {exc}")
        if cuda_available:
            try:
                print(f"torch.cuda.current_device: {cuda.current_device()}")
                print(f"torch.cuda.device_name[0]: {cuda.get_device_name(0)}")
                print(f"torch.cuda.capability[0]: {cuda.get_device_capability(0)}")
            except Exception as exc:  # noqa: BLE001
                print(f"torch.cuda device detail error: {exc.__class__.__name__}: {exc}")
    xpu = getattr(torch, "xpu", None)
    if xpu is not None and hasattr(xpu, "is_available"):
        try:
            print(f"torch.xpu.is_available: {xpu.is_available()}")
        except Exception as exc:  # noqa: BLE001
            print(f"torch.xpu.is_available error: {exc.__class__.__name__}: {exc}")
    try:
        target = triton.runtime.driver.active.get_current_target()
        print(f"triton active target: {target}")
    except Exception as exc:  # noqa: BLE001
        print(f"triton active target: unavailable ({exc.__class__.__name__}: {exc})")
    print()


def print_optional_modules() -> None:
    print("== Optional backend packages ==")
    for module_name, description in OPTIONAL_MODULES.items():
        print(f"{module_name}: {find_optional_module(module_name)} ({description})")
    print()


def print_env_vars() -> None:
    print("== Selected FLA environment variables ==")
    for name in FLA_ENV_VARS:
        print(f"{name}={os.environ.get(name, '<unset>')}")
    print()


def require_cuda(torch: ModuleType) -> bool:
    print("== CUDA allocation check ==")
    cuda = getattr(torch, "cuda", None)
    if cuda is None:
        print("ERROR: torch.cuda module is unavailable", file=sys.stderr)
        return False
    try:
        if not cuda.is_available():
            print("ERROR: torch.cuda.is_available() is False", file=sys.stderr)
            return False
        x = torch.ones((2,), device="cuda")
        y = (x + 1).detach().cpu().tolist()
        cuda.synchronize()
        print(f"tiny CUDA tensor check: ok ({y})")
        print()
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: tiny CUDA tensor check failed: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return False


def main() -> int:
    args = parse_args()
    print_header()

    fla = import_required(
        "fla",
        "Install FLA with a backend extra, e.g. flash-linear-attention[cuda], [rocm], [xpu], [npu], or [cpu].",
    )
    torch = import_required(
        "torch",
        "torch is not a base dependency; install the backend-specific FLA extra and matching PyTorch wheel.",
    )
    triton = import_required(
        "triton",
        "triton or a backend-specific Triton flavor is required by FLA runtime packages.",
    )
    if fla is None or torch is None or triton is None:
        return 2

    print_versions(fla, torch, triton)
    print_export_counts()
    print_torch_backend(torch, triton)
    print_optional_modules()
    if args.show_env_vars:
        print_env_vars()
    if args.require_cuda and not require_cuda(torch):
        return 3

    print("FLA runtime check completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
