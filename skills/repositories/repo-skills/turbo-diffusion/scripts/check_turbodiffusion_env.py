#!/usr/bin/env python3
"""Check TurboDiffusion import, source-layout, CUDA, custom op, and optional SageSLA readiness.

This helper is safe by default: it does not download checkpoints, run video
models, train, or write outside temporary Python objects. Use --repo-root when
checking a source checkout whose scripts require PYTHONPATH-style top-level
imports such as imaginaire, rcm, ops, SLA, serve, or modify_model.
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path


def add_source_layout(repo_root: str | None) -> None:
    if not repo_root:
        return
    root = Path(repo_root).expanduser().resolve()
    candidates = [root / "turbodiffusion", root]
    for candidate in candidates:
        if candidate.is_dir():
            sys.path.insert(0, str(candidate))


def check_import(name: str) -> tuple[bool, str]:
    try:
        mod = importlib.import_module(name)
        return True, getattr(mod, "__file__", "built-in") or "built-in"
    except Exception as exc:  # noqa: BLE001 - diagnostics should catch import errors
        return False, f"{type(exc).__name__}: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check TurboDiffusion environment readiness without running models")
    parser.add_argument("--repo-root", default=None, help="Optional TurboDiffusion source checkout root for source-layout imports")
    parser.add_argument("--require-cuda", action="store_true", help="Exit non-zero if torch CUDA is unavailable")
    parser.add_argument("--require-custom-ops", action="store_true", help="Exit non-zero if turbo_diffusion_ops cannot be imported")
    parser.add_argument("--require-sagesla", action="store_true", help="Exit non-zero if SpargeAttn-backed SageSLA is unavailable")
    parser.add_argument("--skip-tiny-cuda", action="store_true", help="Do not run tiny CUDA allocation/custom-op smoke checks")
    args = parser.parse_args()

    add_source_layout(args.repo_root or os.environ.get("TURBODIFFUSION_REPO_ROOT"))

    failures: list[str] = []

    print("== imports ==")
    for name in ["turbodiffusion", "imaginaire", "rcm.datasets.utils", "SLA", "ops", "serve.arg_utils", "modify_model"]:
        ok, detail = check_import(name)
        print(f"{name}: {'ok' if ok else 'FAIL'} ({detail})")

    custom_ok, custom_detail = check_import("turbo_diffusion_ops")
    print(f"turbo_diffusion_ops: {'ok' if custom_ok else 'FAIL'} ({custom_detail})")
    if args.require_custom_ops and not custom_ok:
        failures.append("custom ops are required but turbo_diffusion_ops did not import")

    print("\n== torch/cuda ==")
    torch_ok, torch_detail = check_import("torch")
    print(f"torch: {'ok' if torch_ok else 'FAIL'} ({torch_detail})")
    cuda_ok = False
    if torch_ok:
        import torch

        cuda_ok = bool(torch.cuda.is_available())
        print(f"torch_version={torch.__version__} torch_cuda={torch.version.cuda} cuda_available={cuda_ok}")
        if cuda_ok:
            print(f"cuda_device_count={torch.cuda.device_count()}")
            print(f"cuda_device_0={torch.cuda.get_device_name(0)} capability={torch.cuda.get_device_capability(0)}")
            if not args.skip_tiny_cuda:
                try:
                    x = torch.empty((1,), device="cuda")
                    print(f"tiny_cuda_allocation=ok device={x.device}")
                except Exception as exc:  # noqa: BLE001
                    print(f"tiny_cuda_allocation=FAIL {type(exc).__name__}: {exc}")
                    failures.append("tiny CUDA allocation failed")
    if args.require_cuda and not cuda_ok:
        failures.append("CUDA is required but torch.cuda.is_available() is false")

    print("\n== optional SageSLA ==")
    try:
        core = importlib.import_module("SLA.core")
        sagesla_enabled = bool(getattr(core, "SAGESLA_ENABLED", False))
        print(f"SAGESLA_ENABLED={sagesla_enabled}")
        if args.require_sagesla and not sagesla_enabled:
            failures.append("SageSLA is required but SpargeAttn-backed SAGESLA_ENABLED is false")
    except Exception as exc:  # noqa: BLE001
        print(f"SLA.core=FAIL {type(exc).__name__}: {exc}")
        if args.require_sagesla:
            failures.append("SageSLA is required but SLA.core did not import")

    print("\n== tiny custom-op smoke ==")
    if custom_ok and torch_ok and cuda_ok and not args.skip_tiny_cuda:
        try:
            import torch
            from ops import FastLayerNorm, FastRMSNorm, int8_quant

            x = torch.randn(128, 128, device="cuda", dtype=torch.bfloat16).contiguous()
            x_q, x_s = int8_quant(x)
            print(f"int8_quant=ok q_dtype={x_q.dtype} scale_shape={tuple(x_s.shape)}")
            y = FastRMSNorm(128).cuda()(x)
            z = FastLayerNorm(128, elementwise_affine=False).cuda()(x)
            print(f"fast_norm=ok rms_finite={bool(torch.isfinite(y).all())} layer_finite={bool(torch.isfinite(z).all())}")
        except Exception as exc:  # noqa: BLE001
            print(f"custom_op_smoke=FAIL {type(exc).__name__}: {exc}")
            if args.require_custom_ops:
                failures.append("custom-op smoke failed")
    else:
        print("custom_op_smoke=skipped")

    if failures:
        print("\nFAILURES:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("\nEnvironment check completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
