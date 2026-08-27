#!/usr/bin/env python3
"""Check whether an environment can import HRM training/evaluation surfaces.

The helper is intentionally bounded: it does not start training, download data,
connect to W&B, or require a checkpoint. Use it before long HRM runs.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


def _add_repo_root(repo_root: Path) -> Path:
    repo_root = repo_root.expanduser().resolve()
    if not (repo_root / "pretrain.py").exists() or not (repo_root / "evaluate.py").exists():
        raise SystemExit(f"repo root does not look like HRM: {repo_root}")
    sys.path.insert(0, os.fspath(repo_root))
    return repo_root


def run_checks(repo_root: Path, require_cuda: bool) -> dict[str, Any]:
    repo_root = _add_repo_root(repo_root)
    import torch
    import pretrain
    import evaluate
    from utils.functions import load_model_class

    report: dict[str, Any] = {
        "repo_root_checked": os.fspath(repo_root),
        "torch_version": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "cuda_available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()),
        "pretrain_config_fields": sorted(pretrain.PretrainConfig.model_fields.keys()),
        "eval_config_fields": sorted(evaluate.EvalConfig.model_fields.keys()),
        "model_class": load_model_class("hrm.hrm_act_v1@HierarchicalReasoningModel_ACTV1").__name__,
        "loss_class": load_model_class("losses@ACTLossHead").__name__,
    }

    if torch.cuda.is_available():
        report["device_name"] = torch.cuda.get_device_name(0)
        report["device_capability"] = list(torch.cuda.get_device_capability(0))
        torch.empty((1,), device="cuda")
    elif require_cuda:
        raise RuntimeError("CUDA is required for HRM train/eval but torch.cuda.is_available() is false")

    missing = []
    for module_name in ["flash_attn", "adam_atan2_backend", "wandb", "hydra", "omegaconf", "argdantic"]:
        try:
            __import__(module_name)
        except Exception as exc:
            missing.append({"module": module_name, "error": str(exc)})
    report["missing_or_failed_modules"] = missing
    if require_cuda and missing:
        raise RuntimeError(f"required CUDA training modules failed: {missing}")

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Check HRM training/evaluation import and CUDA readiness.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Path to the HRM checkout.")
    parser.add_argument("--require-cuda", action="store_true", help="Fail if CUDA/FlashAttention/adam-atan2 backend are unavailable.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    args = parser.parse_args()

    try:
        report = run_checks(args.repo_root, args.require_cuda)
    except Exception as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"ERROR: {exc}")
        return 2

    report["ok"] = True
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"OK: torch {report['torch_version']} cuda={report['torch_cuda']} available={report['cuda_available']}")
        if report.get("device_name"):
            print(f"device: {report['device_name']} capability={report['device_capability']}")
        if report["missing_or_failed_modules"]:
            print("missing/failed optional modules:", report["missing_or_failed_modules"])
        print(f"model={report['model_class']} loss={report['loss_class']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
