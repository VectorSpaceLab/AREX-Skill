#!/usr/bin/env python3
"""Check the installed xTuring environment.

This is a read-only diagnostic. It verifies the core package import, dataset and
 evaluation entry points, model registry shape, CLI help, and optional backend
 availability. Pass --repo-root if you want to inspect an uninstalled checkout.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as md
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from click.testing import CliRunner

REQUIRED_MODEL_KEYS = [
    "distilgpt2",
    "gpt2",
    "generic",
    "mistral_7b",
    "qwen3_0_6b",
    "gpt_oss_20b",
    "minimax_m2",
    "stable_diffusion",
]
OPTIONAL_MODULES = ["anthropic", "bitsandbytes", "deepspeed", "wandb"]


def _add_repo_root(repo_root: str | None) -> None:
    if not repo_root:
        return
    root = Path(repo_root).resolve()
    sys.path.insert(0, str(root))


def _help_check(command, args: List[str]) -> Dict[str, Any]:
    runner = CliRunner()
    result = runner.invoke(command, args)
    return {
        "args": args,
        "exit_code": result.exit_code,
        "ok": result.exit_code == 0,
    }


def _optional_import_status(module_name: str) -> Dict[str, Any]:
    try:
        importlib.import_module(module_name)
        return {"status": "ok"}
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {
            "status": "missing-or-broken",
            "error": str(exc).splitlines()[0],
        }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check the installed xTuring environment and its core entry points."
    )
    parser.add_argument(
        "--repo-root",
        help="Optional repository root to add to sys.path before importing xTuring.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a human summary.",
    )
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="Treat missing CUDA support as a failure.",
    )
    args = parser.parse_args(argv)

    _add_repo_root(args.repo_root)

    try:
        import xturing
        from xturing.cli import xturing as xturing_cli
        from xturing.datasets import InstructionDataset, PreferenceDataset, TextDataset
        from xturing.evaluation import (
            LMEvalAdapter,
            persist_eval_result,
            run_eval_adapter,
        )
        from xturing.models import BaseModel
        import torch
    except Exception as exc:
        print(f"core import failed: {exc}", file=sys.stderr)
        return 1

    report: Dict[str, Any] = {
        "package_version": md.version("xturing"),
        "module_file": str(Path(xturing.__file__).resolve()),
        "datasets": {
            "TextDataset": TextDataset.config_name,
            "InstructionDataset": InstructionDataset.config_name,
            "PreferenceDataset": PreferenceDataset.config_name,
        },
        "evaluation": {
            "LMEvalAdapter": LMEvalAdapter.adapter_name,
            "run_eval_adapter": callable(run_eval_adapter),
            "persist_eval_result": callable(persist_eval_result),
        },
        "cli": {
            "xturing": _help_check(xturing_cli, ["--help"]),
            "chat": _help_check(xturing_cli, ["chat", "--help"]),
            "api": _help_check(xturing_cli, ["api", "--help"]),
            "ui": _help_check(xturing_cli, ["ui", "--help"]),
        },
        "models": {},
        "torch": {
            "version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_device_count": torch.cuda.device_count(),
        },
        "optional": {},
    }

    if torch.cuda.is_available():
        sample = torch.tensor([1.0], device="cuda")
        report["torch"]["cuda_tensor_device"] = str(sample.device)

    try:
        registry_keys = sorted(BaseModel.registry)
        missing = [key for key in REQUIRED_MODEL_KEYS if key not in BaseModel.registry]
        report["models"] = {
            "registry_size": len(registry_keys),
            "required_missing": missing,
            "sample_keys": registry_keys[:12],
        }
        if missing:
            print(
                "missing required model registry keys: " + ", ".join(missing),
                file=sys.stderr,
            )
            return 1
    except Exception as exc:
        print(f"model registry import failed: {exc}", file=sys.stderr)
        return 1

    if args.require_cuda and not report["torch"]["cuda_available"]:
        print("CUDA is required but not available.", file=sys.stderr)
        return 1

    report["optional"] = {
        module_name: _optional_import_status(module_name) for module_name in OPTIONAL_MODULES
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    print(f"xTuring {report['package_version']} @ {report['module_file']}")
    print(f"datasets: {report['datasets']}")
    print(f"evaluation: {report['evaluation']}")
    print(f"models registry size: {report['models']['registry_size']}")
    print(f"cuda available: {report['torch']['cuda_available']}")
    print(f"cli checks: {report['cli']}")
    print(f"optional modules: {report['optional']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
