#!/usr/bin/env python3
"""Smoke-check AutoGluon multimodal imports and APIs without training by default."""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import platform
import sys
from importlib import metadata
from typing import Any, Dict, Sequence


PACKAGES = [
    "autogluon.multimodal",
    "torch",
    "torchvision",
    "transformers",
    "pandas",
    "numpy",
]

OPTIONAL_PACKAGES = [
    "onnx",
    "onnxruntime",
    "tensorrt",
    "mmcv",
    "mmdet",
    "pycocotools",
    "PIL",
    "pdf2image",
    "pytesseract",
]

PROBLEM_TYPES = [
    "classification",
    "binary",
    "multiclass",
    "regression",
    "ner",
    "named_entity_recognition",
    "object_detection",
    "text_similarity",
    "image_similarity",
    "image_text_similarity",
    "feature_extraction",
    "zero_shot_image_classification",
    "few_shot_classification",
    "semantic_segmentation",
]


def version_for(import_name: str) -> str | None:
    candidates = [import_name, import_name.split(".")[0]]
    aliases = {"PIL": "Pillow"}
    candidates.extend(aliases.get(candidate, candidate) for candidate in list(candidates))
    for candidate in candidates:
        try:
            return metadata.version(candidate)
        except metadata.PackageNotFoundError:
            continue
    return None


def import_status(import_name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(import_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic tool should capture all import failures.
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "ok": True,
        "version": version_for(import_name) or getattr(module, "__version__", None),
    }


def get_api_report() -> Dict[str, Any]:
    report: Dict[str, Any] = {}
    try:
        from autogluon.multimodal import MultiModalPredictor
    except Exception as exc:  # noqa: BLE001
        return {"error": f"failed to import MultiModalPredictor: {type(exc).__name__}: {exc}"}

    report["MultiModalPredictor"] = {
        "signature": str(inspect.signature(MultiModalPredictor)),
    }
    for method_name in [
        "fit",
        "predict",
        "predict_proba",
        "evaluate",
        "extract_embedding",
        "save",
        "load",
        "export_onnx",
        "optimize_for_inference",
        "fit_summary",
    ]:
        method = getattr(MultiModalPredictor, method_name, None)
        if method is None:
            report["MultiModalPredictor"][method_name] = "MISSING"
        else:
            report["MultiModalPredictor"][method_name] = str(inspect.signature(method))

    try:
        from autogluon.multimodal.utils.problem_types import PROBLEM_TYPES_REG

        report["problem_types"] = PROBLEM_TYPES_REG.list_keys()
    except Exception as exc:  # noqa: BLE001
        report["problem_types_error"] = f"{type(exc).__name__}: {exc}"
    return report


def get_backend_report(include_optional: bool) -> Dict[str, Any]:
    packages = list(PACKAGES)
    if include_optional:
        packages.extend(OPTIONAL_PACKAGES)
    report = {name: import_status(name) for name in packages}

    torch_status = report.get("torch", {})
    if torch_status.get("ok"):
        try:
            import torch

            torch_status["cuda_available"] = torch.cuda.is_available()
            torch_status["cuda_device_count"] = torch.cuda.device_count()
            torch_status["cuda_version"] = getattr(torch.version, "cuda", None)
        except Exception as exc:  # noqa: BLE001
            torch_status["cuda_error"] = f"{type(exc).__name__}: {exc}"

    ort_status = report.get("onnxruntime", {})
    if ort_status.get("ok"):
        try:
            import onnxruntime as ort

            ort_status["providers"] = ort.get_available_providers()
        except Exception as exc:  # noqa: BLE001
            ort_status["providers_error"] = f"{type(exc).__name__}: {exc}"

    return report


def instantiate_problem_types() -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    try:
        from autogluon.multimodal import MultiModalPredictor
    except Exception as exc:  # noqa: BLE001
        return {"error": f"failed to import MultiModalPredictor: {type(exc).__name__}: {exc}"}

    for problem_type in PROBLEM_TYPES:
        try:
            kwargs: Dict[str, Any] = {"problem_type": problem_type, "verbosity": 0}
            if problem_type == "object_detection":
                kwargs["sample_data_path"] = None
            predictor = MultiModalPredictor(**kwargs)
            results[problem_type] = {"ok": True, "resolved_problem_type": getattr(predictor, "problem_type", None)}
        except Exception as exc:  # noqa: BLE001
            results[problem_type] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check AutoGluon MultiModal imports, API signatures, problem types, and optional backends without training.",
    )
    parser.add_argument("--optional-backends", action="store_true", help="Probe optional ONNX, detection, OCR, and TensorRT packages")
    parser.add_argument("--instantiate", action="store_true", help="Instantiate each registered problem type without fitting or predicting")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "imports": get_backend_report(args.optional_backends),
        "api": get_api_report(),
    }
    if args.instantiate:
        report["instantiation"] = instantiate_problem_types()

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']} ({report['platform']})")
        print("\nImports:")
        for name, status in report["imports"].items():
            if status.get("ok"):
                details = []
                if status.get("version"):
                    details.append(f"version={status['version']}")
                if "cuda_available" in status:
                    details.append(f"cuda_available={status['cuda_available']}")
                    details.append(f"cuda_device_count={status['cuda_device_count']}")
                    details.append(f"cuda_version={status['cuda_version']}")
                if status.get("providers"):
                    details.append(f"providers={status['providers']}")
                print(f"  OK   {name}" + (f" ({', '.join(details)})" if details else ""))
            else:
                print(f"  MISS {name}: {status.get('error')}")
        print("\nAPI:")
        api = report["api"]
        if "error" in api:
            print(f"  {api['error']}")
        else:
            predictor_api = api.get("MultiModalPredictor", {})
            print(f"  MultiModalPredictor{predictor_api.get('signature', '')}")
            for method_name in ["fit", "predict", "predict_proba", "evaluate", "extract_embedding", "save", "load", "export_onnx", "optimize_for_inference"]:
                print(f"  {method_name}{predictor_api.get(method_name, ' MISSING')}")
            if api.get("problem_types"):
                print("\nProblem types:")
                print("  " + ", ".join(api["problem_types"]))
        if args.instantiate:
            print("\nInstantiation:")
            for problem_type, status in report.get("instantiation", {}).items():
                if status.get("ok"):
                    print(f"  OK   {problem_type} -> {status.get('resolved_problem_type')}")
                else:
                    print(f"  FAIL {problem_type}: {status.get('error')}")

    required_failures = [name for name in PACKAGES if not report["imports"].get(name, {}).get("ok")]
    api_failed = "error" in report["api"]
    return 1 if required_failures or api_failed else 0


if __name__ == "__main__":
    sys.exit(main())
