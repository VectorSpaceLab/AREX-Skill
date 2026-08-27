#!/usr/bin/env python3
"""Check a Python environment for Lazy Predict base and optional capabilities.

Example:
    python scripts/check_lazypredict_env.py --json

The script is read-only: it imports modules, checks distribution metadata, and
optionally calls the installed CLI with --version. It never installs packages,
downloads model weights, starts services, or requires the source repository.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any

OPTIONAL_MODULES = {
    "boost:xgboost": "xgboost",
    "boost:lightgbm": "lightgbm",
    "boost:catboost": "catboost",
    "timeseries:statsmodels": "statsmodels",
    "timeseries:pmdarima": "pmdarima",
    "deeplearning:torch": "torch",
    "foundation:timesfm": "timesfm",
    "tune:optuna": "optuna",
    "explain:shap": "shap",
    "interpret:interpret": "interpret",
    "flaml:flaml": "flaml",
    "spark:pyspark": "pyspark",
    "distributed:dask": "dask",
    "mlflow:mlflow": "mlflow",
    "viz:matplotlib": "matplotlib",
    "categorical:category_encoders": "category_encoders",
    "intel:sklearnex": "sklearnex",
    "gpu:cuml": "cuml",
}

PUBLIC_IMPORTS = [
    "lazypredict",
    "lazypredict.Supervised",
    "lazypredict.TimeSeriesForecasting",
    "lazypredict.cli",
    "lazypredict.preprocessing",
    "lazypredict.metrics",
    "lazypredict.config",
    "lazypredict.explainability",
    "lazypredict.tuning",
    "lazypredict.ts_tuning",
    "lazypredict.ensemble",
    "lazypredict.horizon",
    "lazypredict.distributed",
    "lazypredict.spark",
]


def module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def import_status(name: str) -> dict[str, Any]:
    try:
        importlib.import_module(name)
        return {"ok": True}
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def torch_cuda_status() -> dict[str, Any]:
    if not module_available("torch"):
        return {"torch_installed": False, "cuda_available": False}
    try:
        import torch

        info: dict[str, Any] = {
            "torch_installed": True,
            "torch_version": getattr(torch, "__version__", None),
            "cuda_version": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }
        if info["cuda_available"]:
            info["device_0"] = torch.cuda.get_device_name(0)
        return info
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"torch_installed": True, "cuda_available": False, "error": f"{type(exc).__name__}: {exc}"}


def cli_version() -> dict[str, Any]:
    exe = shutil.which("lazypredict")
    if not exe:
        return {"available_on_path": False}
    proc = subprocess.run([exe, "--version"], text=True, capture_output=True, timeout=30)
    return {
        "available_on_path": True,
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Lazy Predict installation and optional dependencies.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--no-cli", action="store_true", help="Skip the CLI --version subprocess check.")
    args = parser.parse_args()

    try:
        dist_version = version("lazypredict")
    except PackageNotFoundError:
        dist_version = None

    report = {
        "python": sys.version.split()[0],
        "distribution": {"lazypredict": dist_version},
        "imports": {name: import_status(name) for name in PUBLIC_IMPORTS},
        "optional_modules": {label: module_available(module) for label, module in OPTIONAL_MODULES.items()},
        "torch_cuda": torch_cuda_status(),
        "cli": None if args.no_cli else cli_version(),
    }
    report["ok"] = bool(dist_version) and all(item["ok"] for item in report["imports"].values())

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Lazy Predict distribution: {dist_version or 'not installed'}")
        print(f"Public imports: {'ok' if all(item['ok'] for item in report['imports'].values()) else 'failed'}")
        if report["cli"] is not None:
            print(f"CLI: {report['cli']}")
        missing = [label for label, ok in report["optional_modules"].items() if not ok]
        print(f"Missing optional modules: {', '.join(missing) if missing else 'none'}")
        print(f"Torch/CUDA: {report['torch_cuda']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
