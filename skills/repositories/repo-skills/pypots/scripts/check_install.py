#!/usr/bin/env python3
"""Safe PyPOTS installation and surface check.

This script imports the installed package (or an explicitly supplied checkout),
prints the version, lists task model counts, lists CLI commands, and reports
optional backend packages. It does not train models, download data, or write
files.

Examples:
    python scripts/check_install.py
    python scripts/check_install.py --repo-root /path/to/PyPOTS --json
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import platform
import sys
from pathlib import Path
from typing import Any


TASK_MODULES = {
    "imputation": "pypots.imputation",
    "classification": "pypots.classification",
    "forecasting": "pypots.forecasting",
    "anomaly_detection": "pypots.anomaly_detection",
    "clustering": "pypots.clustering",
    "representation": "pypots.representation",
}

OPTIONAL_PACKAGES = {
    "torch_geometric": {"module": "torch_geometric", "purpose": "Raindrop graph neural model backend"},
    "torch_scatter": {"module": "torch_scatter", "purpose": "Raindrop graph neural model backend"},
    "torch_sparse": {"module": "torch_sparse", "purpose": "Raindrop graph neural model backend"},
    "sentencepiece": {"module": "sentencepiece", "purpose": "some LLM/tokenizer workflows"},
    "pyyaml": {"module": "yaml", "purpose": "YAML CLI configs"},
    "optuna": {"module": "optuna", "purpose": "pypots-cli tune"},
    "ai4ts": {"module": "ai4ts", "purpose": "pypots-cli data profile and protocol tools"},
    "benchpots": {"module": "benchpots", "purpose": "examples, benchmarks, and synthetic test data"},
    "pygrinder": {"module": "pygrinder", "purpose": "missingness simulation and masks"},
    "tsdb": {"module": "tsdb", "purpose": "dataset loading/cache utilities"},
}


def _maybe_add_repo_root(repo_root: str | None) -> None:
    if not repo_root:
        return
    root = Path(repo_root).expanduser().resolve()
    if not (root / "pypots").is_dir():
        raise SystemExit(f"--repo-root does not look like a PyPOTS checkout: {root}")
    sys.path.insert(0, str(root))


def _model_counts() -> dict[str, Any]:
    counts: dict[str, Any] = {}
    for task, module_name in TASK_MODULES.items():
        try:
            module = importlib.import_module(module_name)
            exports = list(getattr(module, "__all__", []))
            counts[task] = {"count": len(exports), "models": exports}
        except Exception as exc:  # pragma: no cover - diagnostic path
            counts[task] = {"error": f"{type(exc).__name__}: {exc}"}
    return counts


def _cli_commands() -> list[str] | str:
    try:
        from pypots.cli.pypots_cli import cli

        return sorted(cli.list_commands(None))
    except Exception as exc:  # pragma: no cover - diagnostic path
        return f"{type(exc).__name__}: {exc}"


def _torch_info() -> dict[str, Any]:
    try:
        import torch

        info: dict[str, Any] = {
            "version": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()),
            "mps_available": bool(hasattr(torch.backends, "mps") and torch.backends.mps.is_available()),
        }
        if torch.cuda.is_available():
            info["cuda_version"] = torch.version.cuda
            info["cuda_device_names"] = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
        return info
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"error": f"{type(exc).__name__}: {exc}"}


def _optional_status() -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for package, info in OPTIONAL_PACKAGES.items():
        result[package] = {
            "purpose": info["purpose"],
            "status": "installed" if importlib.util.find_spec(info["module"]) else "missing",
            "module": info["module"],
        }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a PyPOTS installation without training or downloads.")
    parser.add_argument("--repo-root", default=None, help="Optional PyPOTS checkout to prepend to sys.path.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    _maybe_add_repo_root(args.repo_root)

    report: dict[str, Any] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
    }

    try:
        import pypots

        report["pypots_version"] = pypots.__version__
    except Exception as exc:
        report["pypots_error"] = f"{type(exc).__name__}: {exc}"
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print("PyPOTS import failed:", report["pypots_error"])
        return 1

    report["torch"] = _torch_info()
    report["tasks"] = _model_counts()
    report["cli_commands"] = _cli_commands()
    report["optional_packages"] = _optional_status()

    has_task_errors = any("error" in value for value in report["tasks"].values())
    has_cli_error = isinstance(report["cli_commands"], str)
    has_torch_error = "error" in report["torch"]

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"PyPOTS version: {report['pypots_version']}")
        print(f"Python: {report['python']}")
        print(f"Platform: {report['platform']}")
        print(f"Torch: {report['torch']}")
        print("\nTask model counts:")
        for task, value in report["tasks"].items():
            if "error" in value:
                print(f"  {task}: ERROR {value['error']}")
            else:
                print(f"  {task}: {value['count']} models")
        print("\nCLI commands:")
        print(f"  {report['cli_commands']}")
        print("\nOptional packages:")
        for package, value in report["optional_packages"].items():
            print(f"  {package:<16} {value['status']:<9} {value['purpose']}")

    return 1 if (has_task_errors or has_cli_error or has_torch_error) else 0


if __name__ == "__main__":
    raise SystemExit(main())
