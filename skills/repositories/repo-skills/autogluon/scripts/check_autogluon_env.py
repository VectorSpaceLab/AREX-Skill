#!/usr/bin/env python3
"""Safe AutoGluon environment diagnostic.

Run this in the user's target Python environment to inspect AutoGluon imports,
public predictor signatures, optional backend availability, and torch CPU/GPU
state without training models or downloading assets.

Example:
    python scripts/check_autogluon_env.py --json --optional-backends
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import inspect
import json
import platform
import sys
from typing import Any


CORE_MODULES = [
    "autogluon.common",
    "autogluon.core",
    "autogluon.features",
    "autogluon.tabular",
    "autogluon.timeseries",
    "autogluon.multimodal",
]

DISTRIBUTIONS = [
    "autogluon",
    "autogluon.common",
    "autogluon.core",
    "autogluon.features",
    "autogluon.tabular",
    "autogluon.timeseries",
    "autogluon.multimodal",
]

PREDICTOR_OBJECTS = {
    "TabularPredictor": "autogluon.tabular.TabularPredictor",
    "TimeSeriesPredictor": "autogluon.timeseries.TimeSeriesPredictor",
    "TimeSeriesDataFrame": "autogluon.timeseries.TimeSeriesDataFrame",
    "MultiModalPredictor": "autogluon.multimodal.MultiModalPredictor",
}

OPTIONAL_BACKENDS = [
    "torch",
    "torchvision",
    "lightgbm",
    "catboost",
    "xgboost",
    "ray",
    "onnx",
    "onnxruntime",
    "tensorrt",
    "pytesseract",
    "pdf2image",
    "cv2",
]


def import_status(module_name: str) -> dict[str, Any]:
    item: dict[str, Any] = {"module": module_name, "ok": False}
    try:
        module = importlib.import_module(module_name)
        item.update(
            {
                "ok": True,
                "version": getattr(module, "__version__", None),
                "file_present": bool(getattr(module, "__file__", None)),
            }
        )
    except Exception as exc:
        item["error"] = f"{type(exc).__name__}: {exc}"
    return item


def distribution_status(name: str) -> dict[str, Any]:
    item: dict[str, Any] = {"distribution": name, "ok": False}
    try:
        dist = metadata.distribution(name)
        item.update(
            {
                "ok": True,
                "metadata_name": dist.metadata.get("Name"),
                "version": dist.version,
                "requires_python": dist.metadata.get("Requires-Python"),
            }
        )
    except Exception as exc:
        item["error"] = f"{type(exc).__name__}: {exc}"
    return item


def object_signature(label: str, dotted_path: str) -> dict[str, Any]:
    item: dict[str, Any] = {"name": label, "object": dotted_path, "ok": False}
    try:
        module_name, object_name = dotted_path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        obj = getattr(module, object_name)
        item["ok"] = True
        item["signature"] = str(inspect.signature(obj))
        for method in ["fit", "predict", "predict_proba", "evaluate", "leaderboard", "feature_importance", "save", "load"]:
            if hasattr(obj, method):
                try:
                    item[method] = str(inspect.signature(getattr(obj, method)))
                except Exception as exc:
                    item[method] = f"uninspectable: {type(exc).__name__}: {exc}"
    except Exception as exc:
        item["error"] = f"{type(exc).__name__}: {exc}"
    return item


def torch_status() -> dict[str, Any]:
    item: dict[str, Any] = {"ok": False}
    try:
        import torch

        item.update(
            {
                "ok": True,
                "version": getattr(torch, "__version__", None),
                "cuda_version": getattr(torch.version, "cuda", None),
                "cuda_available": bool(torch.cuda.is_available()),
                "cuda_device_count": int(torch.cuda.device_count()),
            }
        )
        if torch.cuda.is_available():
            item["cuda_device_0"] = torch.cuda.get_device_name(0)
            item["cuda_capability_0"] = list(torch.cuda.get_device_capability(0))
    except Exception as exc:
        item["error"] = f"{type(exc).__name__}: {exc}"
    return item


def collect(args: argparse.Namespace) -> dict[str, Any]:
    report: dict[str, Any] = {
        "python": {
            "version": sys.version.replace("\n", " "),
            "executable_present": bool(sys.executable),
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "distributions": [distribution_status(name) for name in DISTRIBUTIONS],
        "imports": [import_status(name) for name in CORE_MODULES],
        "predictors": [object_signature(name, path) for name, path in PREDICTOR_OBJECTS.items()],
        "torch": torch_status(),
    }
    if args.optional_backends:
        report["optional_backends"] = [import_status(name) for name in OPTIONAL_BACKENDS]
    return report


def print_text(report: dict[str, Any]) -> None:
    print("AutoGluon environment diagnostic")
    print(f"Python: {report['python']['version'].split()[0]} ({report['python']['platform']})")
    print("\nDistributions:")
    for item in report["distributions"]:
        status = "OK" if item["ok"] else "MISSING"
        version = item.get("version") or item.get("error")
        print(f"  {status:7} {item['distribution']}: {version}")
    print("\nImports:")
    for item in report["imports"]:
        status = "OK" if item["ok"] else "FAIL"
        detail = item.get("version") or item.get("error") or ""
        print(f"  {status:4} {item['module']}: {detail}")
    print("\nPredictors:")
    for item in report["predictors"]:
        status = "OK" if item["ok"] else "FAIL"
        detail = item.get("signature") or item.get("error") or ""
        print(f"  {status:4} {item['name']}: {detail}")
    torch = report["torch"]
    print("\nTorch:")
    if torch.get("ok"):
        print(
            f"  OK torch={torch.get('version')} cuda={torch.get('cuda_version')} "
            f"cuda_available={torch.get('cuda_available')} devices={torch.get('cuda_device_count')}"
        )
    else:
        print(f"  FAIL {torch.get('error')}")
    if "optional_backends" in report:
        print("\nOptional backends:")
        for item in report["optional_backends"]:
            status = "OK" if item["ok"] else "MISSING"
            detail = item.get("version") or item.get("error") or ""
            print(f"  {status:7} {item['module']}: {detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check AutoGluon imports, versions, predictor signatures, and optional backends.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--optional-backends", action="store_true", help="Probe optional packages such as Ray, ONNX, OCR/PDF, and detection/export dependencies.")
    args = parser.parse_args()

    report = collect(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)

    required_imports_ok = all(item["ok"] for item in report["imports"])
    predictors_ok = all(item["ok"] for item in report["predictors"])
    return 0 if required_imports_ok and predictors_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
