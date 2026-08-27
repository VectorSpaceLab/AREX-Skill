#!/usr/bin/env python3
"""Check an Optuna environment without requiring the original repository checkout.

Example:
    python scripts/check_optuna_env.py
"""

from __future__ import annotations

import importlib.metadata as metadata
import importlib.util
import json
import shutil
import subprocess
import sys


def has_module(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


def main() -> int:
    try:
        import optuna
    except Exception as exc:
        print(f"FAILED: cannot import optuna: {type(exc).__name__}: {exc}")
        return 1

    try:
        dist_version = metadata.version("optuna")
    except metadata.PackageNotFoundError:
        dist_version = None

    study = optuna.create_study(direction="minimize")
    study.optimize(lambda trial: (trial.suggest_float("x", -1.0, 1.0) - 0.25) ** 2, n_trials=3)

    cli = shutil.which("optuna")
    cli_help_ok = False
    if cli:
        result = subprocess.run([cli, "--help"], text=True, capture_output=True, timeout=20)
        cli_help_ok = result.returncode == 0 and "create-study" in result.stdout

    optional_modules = {
        "plotly": "plotly",
        "matplotlib": "matplotlib",
        "pandas": "pandas",
        "scikit-learn": "sklearn",
        "scipy": "scipy",
        "torch": "torch",
        "cmaes": "cmaes",
        "boto3": "boto3",
        "google-cloud-storage": "google.cloud.storage",
        "redis": "redis",
        "grpcio": "grpc",
    }

    report = {
        "python": sys.version.split()[0],
        "optuna_import_version": getattr(optuna, "__version__", None),
        "optuna_distribution_version": dist_version,
        "minimal_study_ok": study.best_value is not None,
        "cli_on_path": bool(cli),
        "cli_help_ok": cli_help_ok,
        "optional_modules": {name: has_module(module) for name, module in optional_modules.items()},
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["minimal_study_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
