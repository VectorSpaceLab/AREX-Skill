#!/usr/bin/env python3
"""Inspect the installed Auto-PyTorch package from a target Python.

This script is intentionally lightweight:
- it does not train models
- it does not download datasets
- it only imports public modules and prints signatures

Run it after installation to confirm that the core tabular and forecasting APIs
are importable from the environment you intend to use.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Dict


def _safe_import(path: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(path)
        return {"ok": True, "module": path, "file": getattr(module, "__file__", None)}
    except Exception as exc:  # pragma: no cover - inspection helper
        return {"ok": False, "module": path, "error": f"{type(exc).__name__}: {exc}"}


def _safe_signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except Exception as exc:  # pragma: no cover - inspection helper
        return f"<unavailable: {type(exc).__name__}: {exc}>"


def build_report() -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "package": {},
        "imports": {},
        "signatures": {},
        "torch": {},
    }

    try:
        report["package"]["version"] = version("autoPyTorch")
    except PackageNotFoundError:
        report["package"]["version"] = None

    try:
        import autoPyTorch

        report["package"]["module_file"] = getattr(autoPyTorch, "__file__", None)
        report["package"]["module_version"] = getattr(autoPyTorch, "__version__", None)
    except Exception as exc:  # pragma: no cover - inspection helper
        report["package"]["import_error"] = f"{type(exc).__name__}: {exc}"
        return report

    imports = [
        "autoPyTorch.api.tabular_classification",
        "autoPyTorch.api.tabular_regression",
        "autoPyTorch.api.time_series_forecasting",
        "autoPyTorch.api.base_task",
        "autoPyTorch.data.tabular_validator",
        "autoPyTorch.data.time_series_forecasting_validator",
        "autoPyTorch.utils.pipeline",
        "autoPyTorch.utils.results_visualizer",
    ]
    for path in imports:
        report["imports"][path] = _safe_import(path)

    try:
        import torch

        report["torch"] = {
            "version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "cuda_available": torch.cuda.is_available(),
            "cuda_device_count": torch.cuda.device_count(),
        }
    except Exception as exc:  # pragma: no cover - inspection helper
        report["torch"] = {"error": f"{type(exc).__name__}: {exc}"}

    try:
        from autoPyTorch.api.base_task import BaseTask
        from autoPyTorch.api.tabular_classification import TabularClassificationTask
        from autoPyTorch.api.tabular_regression import TabularRegressionTask
        from autoPyTorch.api.time_series_forecasting import TimeSeriesForecastingTask
        from autoPyTorch.data.tabular_validator import TabularInputValidator
        from autoPyTorch.data.time_series_forecasting_validator import (
            TimeSeriesForecastingInputValidator,
        )
        from autoPyTorch.utils.pipeline import get_configuration_space, get_dataset_requirements
        from autoPyTorch.utils.results_visualizer import ColorLabelSettings, PlotSettingParams

        report["signatures"] = {
            "BaseTask.fit_pipeline": _safe_signature(BaseTask.fit_pipeline),
            "BaseTask.refit": _safe_signature(BaseTask.refit),
            "BaseTask.predict": _safe_signature(BaseTask.predict),
            "BaseTask.score": _safe_signature(BaseTask.score),
            "TabularClassificationTask.search": _safe_signature(TabularClassificationTask.search),
            "TabularRegressionTask.search": _safe_signature(TabularRegressionTask.search),
            "TimeSeriesForecastingTask.search": _safe_signature(TimeSeriesForecastingTask.search),
            "TabularInputValidator.__init__": _safe_signature(TabularInputValidator.__init__),
            "TimeSeriesForecastingInputValidator.__init__": _safe_signature(TimeSeriesForecastingInputValidator.__init__),
            "get_dataset_requirements": _safe_signature(get_dataset_requirements),
            "get_configuration_space": _safe_signature(get_configuration_space),
            "PlotSettingParams": _safe_signature(PlotSettingParams),
            "ColorLabelSettings": _safe_signature(ColorLabelSettings),
        }
    except Exception as exc:  # pragma: no cover - inspection helper
        report["signatures_error"] = f"{type(exc).__name__}: {exc}"

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON instead of a human summary")
    args = parser.parse_args()

    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"autoPyTorch version: {report['package'].get('version')}")
        print(f"package file: {report['package'].get('module_file')}")
        print(f"torch: {report.get('torch')}")
        print("imports:")
        for name, info in report["imports"].items():
            print(f"  - {name}: {'ok' if info.get('ok') else info.get('error')}")
        print("signatures:")
        for name, sig in report.get("signatures", {}).items():
            print(f"  - {name}: {sig}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
