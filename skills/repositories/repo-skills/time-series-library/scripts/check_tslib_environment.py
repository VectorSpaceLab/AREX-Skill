#!/usr/bin/env python3
"""Safe TSLib environment/source-tree preflight checks.

Run from a Time-Series-Library checkout, or pass --repo-root. This script does
not train, download data, or download model weights.
"""
from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from pathlib import Path

CORE_IMPORTS = [
    "data_provider.data_factory",
    "data_provider.data_loader",
    "data_provider.uea",
    "data_provider.m4",
    "exp.exp_long_term_forecasting",
    "exp.exp_short_term_forecasting",
    "exp.exp_imputation",
    "exp.exp_anomaly_detection",
    "exp.exp_classification",
    "exp.exp_zero_shot_forecasting",
    "utils.metrics",
    "utils.losses",
    "utils.tools",
    "layers.SelfAttention_Family",
]
DEFAULT_MODELS = ["DLinear", "TimesNet", "TimeXer", "PatchTST", "Reformer"]
OPTIONAL_MODELS = ["Mamba", "MambaSingleLayer", "Chronos", "Chronos2", "TimesFM", "Moirai", "TiRex", "Sundial", "TimeMoE"]


def try_import(module: str) -> dict:
    try:
        mod = importlib.import_module(module)
        return {"module": module, "ok": True, "file": str(getattr(mod, "__file__", ""))}
    except Exception as exc:  # keep broad: optional model imports can raise runtime import errors
        return {"module": module, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a Time-Series-Library source checkout without training.")
    parser.add_argument("--repo-root", default=".", help="Path to the TSLib source tree containing run.py.")
    parser.add_argument("--check-core-imports", action="store_true", help="Import core data/exp/utils/layers modules.")
    parser.add_argument("--check-torch", action="store_true", help="Report torch and optional CUDA availability.")
    parser.add_argument("--models", nargs="*", default=DEFAULT_MODELS, help="Model module names to import from models/.")
    parser.add_argument("--optional-models", action="store_true", help="Also probe optional Mamba/LTSM model imports and report missing deps as warnings.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    result = {"repo_root": str(root), "checks": []}
    if not (root / "run.py").exists():
        result["checks"].append({"name": "run.py", "ok": False, "error": "run.py not found"})
        print(json.dumps(result, indent=2) if args.json else "FAIL run.py not found")
        return 2

    sys.path.insert(0, str(root))

    help_cmd = [sys.executable, str(root / "run.py"), "--help"]
    proc = subprocess.run(help_cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    result["checks"].append({"name": "run.py --help", "ok": proc.returncode == 0, "returncode": proc.returncode, "stdout_head": proc.stdout.splitlines()[:8], "stderr_head": proc.stderr.splitlines()[:8]})

    if args.check_torch:
        torch_info = {"name": "torch", "ok": False}
        try:
            import torch
            torch_info.update({
                "ok": True,
                "version": getattr(torch, "__version__", None),
                "cuda_version": getattr(getattr(torch, "version", None), "cuda", None),
                "cuda_available": bool(torch.cuda.is_available()),
                "cuda_device_count": int(torch.cuda.device_count()) if hasattr(torch, "cuda") else 0,
            })
            if torch.cuda.is_available():
                torch_info["cuda_device_0"] = torch.cuda.get_device_name(0)
                torch.empty((1,), device="cuda")
        except Exception as exc:
            torch_info["error"] = f"{type(exc).__name__}: {exc}"
        result["checks"].append(torch_info)

    if args.check_core_imports:
        for module in CORE_IMPORTS:
            item = try_import(module)
            item["name"] = "import"
            result["checks"].append(item)

    for model in args.models:
        item = try_import(f"models.{model}")
        item["name"] = "model_import"
        result["checks"].append(item)

    if args.optional_models:
        for model in OPTIONAL_MODELS:
            item = try_import(f"models.{model}")
            item["name"] = "optional_model_import"
            item["optional"] = True
            result["checks"].append(item)

    failed_required = [c for c in result["checks"] if not c.get("ok") and not c.get("optional")]
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for c in result["checks"]:
            status = "OK" if c.get("ok") else ("OPTIONAL-BLOCK" if c.get("optional") else "FAIL")
            label = c.get("module") or c.get("name")
            print(status, label, c.get("error", ""))
    return 1 if failed_required else 0


if __name__ == "__main__":
    raise SystemExit(main())
