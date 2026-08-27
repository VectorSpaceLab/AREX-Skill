#!/usr/bin/env python3
"""Check SplaTAM runtime imports and CUDA readiness.

This helper is safe: it imports modules and allocates a tiny CUDA tensor when
requested, but it does not download data, open a viewer, stream DDS frames, or
run a reconstruction.

Example:
  python scripts/check_env.py --require-cuda --require-rasterizer
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import traceback
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str = ""
    version: str | None = None


def _module_version(module: Any) -> str | None:
    return getattr(module, "__version__", None)


def check_import(module_name: str, label: str | None = None, attr: str | None = None) -> CheckResult:
    label = label or module_name
    try:
        module = importlib.import_module(module_name)
        if attr is not None:
            getattr(module, attr)
        return CheckResult(label, "PASS", version=_module_version(module))
    except Exception as exc:  # pragma: no cover - diagnostic path
        return CheckResult(label, "FAIL", f"{type(exc).__name__}: {exc}")


def check_torch(require_cuda: bool) -> list[CheckResult]:
    results: list[CheckResult] = []
    try:
        import torch

        results.append(CheckResult("torch", "PASS", f"torch_cuda={torch.version.cuda}", torch.__version__))
        cuda_available = bool(torch.cuda.is_available())
        device_count = torch.cuda.device_count() if cuda_available else 0
        status = "PASS" if (cuda_available or not require_cuda) else "FAIL"
        detail = f"cuda_available={cuda_available}, device_count={device_count}"
        if cuda_available:
            try:
                name = torch.cuda.get_device_name(0)
                cap = torch.cuda.get_device_capability(0)
                probe = torch.ones(1, device="cuda")
                detail += f", device0={name}, capability={cap}, tiny_tensor={float(probe.item())}"
            except Exception as exc:  # pragma: no cover - diagnostic path
                status = "FAIL"
                detail += f", cuda_probe_error={type(exc).__name__}: {exc}"
        results.append(CheckResult("torch-cuda", status, detail))
    except Exception as exc:  # pragma: no cover - diagnostic path
        results.append(CheckResult("torch", "FAIL", f"{type(exc).__name__}: {exc}"))
    return results


def check_rasterizer(required: bool) -> CheckResult:
    try:
        module = importlib.import_module("diff_gaussian_rasterization")
        getattr(module, "GaussianRasterizer")
        getattr(module, "GaussianRasterizationSettings")
        return CheckResult("diff_gaussian_rasterization", "PASS", version=_module_version(module))
    except Exception as exc:  # pragma: no cover - diagnostic path
        status = "FAIL" if required else "WARN"
        return CheckResult("diff_gaussian_rasterization", status, f"{type(exc).__name__}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check SplaTAM Python/CUDA/rasterizer readiness.")
    parser.add_argument("--require-cuda", action="store_true", help="Fail when torch CUDA is unavailable.")
    parser.add_argument("--require-rasterizer", action="store_true", help="Fail when diff_gaussian_rasterization cannot import.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument("--tracebacks", action="store_true", help="Print a traceback if the checker itself crashes.")
    args = parser.parse_args()

    try:
        results: list[CheckResult] = []
        results.extend(check_torch(require_cuda=args.require_cuda))
        results.extend([
            check_import("torchvision"),
            check_import("open3d"),
            check_import("cv2"),
            check_import("wandb"),
            check_import("pytorch_msssim"),
            check_import("plyfile"),
            check_import("cyclonedds"),
            check_import("torchmetrics.image.lpip", "torchmetrics.image.lpip", "LearnedPerceptualImagePatchSimilarity"),
            check_rasterizer(required=args.require_rasterizer),
        ])
    except Exception:  # pragma: no cover - defensive diagnostic path
        if args.tracebacks:
            traceback.print_exc()
        return 2

    failed = [r for r in results if r.status == "FAIL"]

    if args.json:
        print(json.dumps({"results": [asdict(r) for r in results], "ok": not failed}, indent=2))
    else:
        for result in results:
            version = f" version={result.version}" if result.version else ""
            detail = f" :: {result.detail}" if result.detail else ""
            print(f"[{result.status}] {result.name}{version}{detail}")
        if failed:
            print("\nSplaTAM environment check failed for required components.", file=sys.stderr)
            print("See references/troubleshooting.md for repair guidance.", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
