#!/usr/bin/env python3
"""Inspect HRM model/loss config identifiers and optional CUDA readiness.

This helper is for future agents using an HRM checkout or installed source copy.
It imports public HRM modules from an explicit repo root, validates model/loss
identifiers, prints config fields, and can run a bounded CUDA dependency smoke.
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import sys
from pathlib import Path
from typing import Any


def _add_repo_root(repo_root: Path) -> None:
    repo_root = repo_root.expanduser().resolve()
    if not (repo_root / "models").exists() or not (repo_root / "config").exists():
        raise SystemExit(f"repo root does not look like HRM: {repo_root}")
    sys.path.insert(0, os.fspath(repo_root))


def _resolve_identifier(identifier: str, prefix: str = "models.") -> Any:
    if "@" not in identifier:
        raise ValueError(f"identifier must have module@class form, got {identifier!r}")
    module_path, class_name = identifier.split("@", 1)
    module = importlib.import_module(prefix + module_path)
    return getattr(module, class_name)


def inspect_config(repo_root: Path) -> dict[str, Any]:
    _add_repo_root(repo_root)
    from models.hrm.hrm_act_v1 import HierarchicalReasoningModel_ACTV1Config, HierarchicalReasoningModel_ACTV1
    from models.losses import ACTLossHead, stablemax_cross_entropy, softmax_cross_entropy
    from utils.functions import load_model_class

    model_identifier = "hrm.hrm_act_v1@HierarchicalReasoningModel_ACTV1"
    loss_identifier = "losses@ACTLossHead"
    model_cls = load_model_class(model_identifier)
    loss_cls = load_model_class(loss_identifier)
    if model_cls is not HierarchicalReasoningModel_ACTV1:
        raise RuntimeError("model identifier did not resolve to HierarchicalReasoningModel_ACTV1")
    if loss_cls is not ACTLossHead:
        raise RuntimeError("loss identifier did not resolve to ACTLossHead")

    return {
        "model_identifier": model_identifier,
        "loss_identifier": loss_identifier,
        "model_class": model_cls.__name__,
        "loss_class": loss_cls.__name__,
        "config_fields": sorted(HierarchicalReasoningModel_ACTV1Config.model_fields.keys()),
        "act_loss_signature": str(inspect.signature(ACTLossHead)),
        "stablemax_signature": str(inspect.signature(stablemax_cross_entropy)),
        "softmax_signature": str(inspect.signature(softmax_cross_entropy)),
    }


def cuda_dependency_smoke(repo_root: Path) -> dict[str, Any]:
    _add_repo_root(repo_root)
    import torch

    result: dict[str, Any] = {
        "torch_version": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "cuda_available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()),
    }
    if not torch.cuda.is_available():
        raise RuntimeError("torch.cuda.is_available() is false; HRM training/evaluation requires CUDA")
    result["device_name"] = torch.cuda.get_device_name(0)
    result["device_capability"] = list(torch.cuda.get_device_capability(0))
    torch.empty((1,), device="cuda")

    try:
        from flash_attn import flash_attn_func
        q = torch.randn(1, 4, 1, 16, device="cuda", dtype=torch.float16)
        out = flash_attn_func(q=q, k=q, v=q, causal=False)
        result["flash_attn"] = {"ok": True, "out_shape": list(out.shape), "out_dtype": str(out.dtype)}
    except Exception as exc:
        raise RuntimeError(f"FlashAttention smoke failed: {exc}") from exc

    try:
        import adam_atan2_backend
        result["adam_atan2_backend"] = {"ok": hasattr(adam_atan2_backend, "adam_atan2_cuda_impl_")}
    except Exception as exc:
        raise RuntimeError(f"adam_atan2_backend import failed: {exc}") from exc

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect HRM model identifiers, config fields, and CUDA dependencies.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Path to an HRM checkout or source tree.")
    parser.add_argument("--cuda-smoke", action="store_true", help="Also run CUDA, FlashAttention, and adam-atan2 backend smokes.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a readable summary.")
    args = parser.parse_args()

    report = {"config": inspect_config(args.repo_root)}
    if args.cuda_smoke:
        report["cuda_smoke"] = cuda_dependency_smoke(args.repo_root)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        cfg = report["config"]
        print(f"model: {cfg['model_identifier']} -> {cfg['model_class']}")
        print(f"loss: {cfg['loss_identifier']} -> {cfg['loss_class']}")
        print("config fields:", ", ".join(cfg["config_fields"]))
        if "cuda_smoke" in report:
            smoke = report["cuda_smoke"]
            print(f"CUDA: torch={smoke['torch_version']} runtime={smoke['torch_cuda']} device={smoke['device_name']}")
            print(f"FlashAttention: {smoke['flash_attn']}")
            print(f"adam_atan2_backend: {smoke['adam_atan2_backend']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
