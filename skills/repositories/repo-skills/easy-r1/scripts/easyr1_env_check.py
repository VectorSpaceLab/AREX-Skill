#!/usr/bin/env python3
"""Safe EasyR1 environment checker.

This helper verifies selected EasyR1 imports and optional backend visibility. It
never downloads models, starts Ray, initializes vLLM, compiles flash-attn, or
runs training.

Examples:
  python scripts/easyr1_env_check.py
  python scripts/easyr1_env_check.py --json
  python scripts/easyr1_env_check.py --require-cuda
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import asdict, dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import Any


CORE_IMPORTS = [
    "verl",
    "verl.protocol",
    "verl.trainer.core_algos",
    "verl.utils.dataset",
    "verl.utils.checkpoint",
    "verl.workers.reward.function",
]
OPTIONAL_IMPORTS = ["ray", "vllm", "flash_attn", "torch", "transformers", "datasets", "qwen_vl_utils"]


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def import_check(module: str) -> CheckResult:
    try:
        imported = importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - diagnostic tool
        return CheckResult(module, False, f"{type(exc).__name__}: {exc}")
    return CheckResult(module, True, getattr(imported, "__file__", "built-in-or-namespace"))


def dist_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def torch_backend(require_cuda: bool) -> dict[str, Any]:
    result: dict[str, Any] = {"available": False, "cuda": None, "error": None}
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"torch import failed: {type(exc).__name__}: {exc}"
        return result

    result["available"] = True
    result["torch_version"] = getattr(torch, "__version__", "unknown")
    result["torch_cuda_version"] = getattr(torch.version, "cuda", None)
    cuda_info: dict[str, Any] = {
        "is_available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
    }
    if torch.cuda.is_available():
        try:
            tensor = torch.empty((1,), device="cuda")
            cuda_info["allocation"] = str(tensor.device)
            cuda_info["device_name_0"] = torch.cuda.get_device_name(0)
            cuda_info["capability_0"] = torch.cuda.get_device_capability(0)
        except Exception as exc:  # noqa: BLE001
            cuda_info["allocation_error"] = f"{type(exc).__name__}: {exc}"
    elif require_cuda:
        cuda_info["error"] = "CUDA was required but torch.cuda.is_available() is false."
    result["cuda"] = cuda_info
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Check EasyR1 imports and optional CUDA visibility without running training.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--require-cuda", action="store_true", help="Exit non-zero if PyTorch CUDA is unavailable.")
    parser.add_argument(
        "--check-optional",
        action="store_true",
        help="Also import optional heavy modules when installed; failures are reported but only vLLM/flash-attn are not required unless their workflows need them.",
    )
    args = parser.parse_args()

    core = [import_check(m) for m in CORE_IMPORTS]
    optional = [import_check(m) for m in OPTIONAL_IMPORTS] if args.check_optional else []
    backend = torch_backend(args.require_cuda)

    payload = {
        "python": sys.version.split()[0],
        "distributions": {name: dist_version(name) for name in ["verl", "torch", "ray", "vllm", "flash-attn", "transformers"]},
        "core_imports": [asdict(item) for item in core],
        "optional_imports": [asdict(item) for item in optional],
        "backend": backend,
        "notes": [
            "This check does not prove full EasyR1 training readiness.",
            "Full training still needs compatible CUDA, Ray, vLLM, flash-attn, model weights, datasets, and GPU memory.",
        ],
    }

    core_ok = all(item.ok for item in core)
    cuda_ok = bool(backend.get("cuda", {}).get("is_available")) if args.require_cuda else True

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    else:
        print(f"Python: {payload['python']}")
        print("Distributions:")
        for name, ver in payload["distributions"].items():
            print(f"  {name}: {ver or 'not installed'}")
        print("Core imports:")
        for item in core:
            status = "ok" if item.ok else "FAILED"
            print(f"  {status:6} {item.name}: {item.detail}")
        if optional:
            print("Optional imports:")
            for item in optional:
                status = "ok" if item.ok else "FAILED"
                print(f"  {status:6} {item.name}: {item.detail}")
        print("Backend:")
        print(json.dumps(backend, indent=2, default=str))
        print("Note: CPU/API checks do not prove full EasyR1 training readiness.")

    return 0 if core_ok and cuda_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
