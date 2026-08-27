#!/usr/bin/env python3
"""Check MiniMind runtime dependencies and backend availability.

This helper performs import and metadata checks only. It does not download
models/data, start services, load large weights, or change the environment.
Use --module-root when checking an explicit MiniMind source tree.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any

CORE_MODULES = ["torch", "transformers", "datasets"]
MINIMIND_MODULES = [
    "model.model_minimind",
    "model.model_lora",
    "dataset.lm_dataset",
    "trainer.trainer_utils",
    "trainer.rollout_engine",
]


def check_import(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - report actionable import failures
        return {"ok": False, "error": str(exc)}
    return {
        "ok": True,
        "version": getattr(module, "__version__", None),
        "file": getattr(module, "__file__", None),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check MiniMind dependencies, CUDA, Qwen3 classes, and optional source modules.")
    parser.add_argument("--module-root", help="Optional MiniMind source tree to prepend to sys.path.")
    parser.add_argument("--check-cuda", action="store_true", help="Require torch.cuda.is_available().")
    parser.add_argument("--check-qwen3", action="store_true", help="Require Qwen3/Qwen3MoE classes from Transformers.")
    parser.add_argument("--check-modules", action="store_true", help="Check MiniMind source modules in addition to core dependencies.")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable report.")
    args = parser.parse_args(argv)

    if args.module_root:
        root = Path(args.module_root).expanduser().resolve()
        if not root.exists():
            report = {"ok": False, "errors": [f"module root does not exist: {root}"], "imports": {}}
            print(json.dumps(report, indent=2) if args.json else report["errors"][0])
            return 1
        sys.path.insert(0, str(root))

    report: dict[str, Any] = {
        "ok": True,
        "python": sys.version.split()[0],
        "imports": {},
        "cuda": None,
        "qwen3": None,
        "module_root": str(Path(args.module_root).expanduser().resolve()) if args.module_root else None,
        "errors": [],
        "warnings": [],
    }

    for name in CORE_MODULES:
        result = check_import(name)
        report["imports"][name] = result
        if not result["ok"]:
            report["errors"].append(f"missing or broken core import {name}: {result['error']}")

    try:
        import torch  # type: ignore

        report["cuda"] = {
            "available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            "torch_version": getattr(torch, "__version__", None),
        }
        if args.check_cuda and not torch.cuda.is_available():
            report["errors"].append("CUDA was requested but torch.cuda.is_available() is false")
    except Exception as exc:  # pragma: no cover - core import error already reported
        report["cuda"] = {"available": False, "error": str(exc)}
        if args.check_cuda:
            report["errors"].append(f"CUDA check failed: {exc}")

    if args.check_qwen3:
        try:
            from transformers import Qwen3Config, Qwen3ForCausalLM, Qwen3MoeConfig, Qwen3MoeForCausalLM  # noqa: F401

            report["qwen3"] = {"ok": True, "classes": ["Qwen3Config", "Qwen3ForCausalLM", "Qwen3MoeConfig", "Qwen3MoeForCausalLM"]}
        except Exception as exc:  # noqa: BLE001
            report["qwen3"] = {"ok": False, "error": str(exc)}
            report["errors"].append(f"Qwen3 class check failed: {exc}")

    if args.check_modules:
        for name in MINIMIND_MODULES:
            result = check_import(name)
            report["imports"][name] = result
            if not result["ok"]:
                report["errors"].append(f"MiniMind source import failed for {name}: {result['error']}")

    if not args.check_cuda and report["cuda"] and not report["cuda"].get("available"):
        report["warnings"].append("CUDA is unavailable; CPU checks do not prove GPU training or generation.")
    report["ok"] = not report["errors"]

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"python={report['python']} status={'OK' if report['ok'] else 'FAILED'}")
        for name, result in report["imports"].items():
            print(f"{name}: {'OK' if result.get('ok') else 'FAIL'}")
        if report["cuda"] is not None:
            print(f"cuda_available={report['cuda'].get('available')}")
        for warning in report["warnings"]:
            print(f"WARNING: {warning}")
        for error in report["errors"]:
            print(f"ERROR: {error}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
