#!/usr/bin/env python3
"""Check optional framework dependencies for BentoML model helpers without installing anything."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FrameworkCheck:
    helper: str
    imports: tuple[str, ...]
    note: str


FRAMEWORKS: dict[str, FrameworkCheck] = {
    "sklearn": FrameworkCheck("bentoml.sklearn", ("sklearn",), "scikit-learn helper"),
    "pytorch": FrameworkCheck("bentoml.pytorch", ("torch",), "PyTorch nn.Module helper"),
    "torchscript": FrameworkCheck("bentoml.torchscript", ("torch",), "TorchScript helper"),
    "pytorch_lightning": FrameworkCheck(
        "bentoml.pytorch_lightning",
        ("torch", "pytorch_lightning"),
        "PyTorch Lightning helper",
    ),
    "tensorflow": FrameworkCheck("bentoml.tensorflow", ("tensorflow",), "TensorFlow helper"),
    "keras": FrameworkCheck("bentoml.keras", ("tensorflow",), "Keras helper uses TensorFlow backend"),
    "transformers": FrameworkCheck("bentoml.transformers", ("transformers",), "Hugging Face Transformers helper"),
    "diffusers": FrameworkCheck(
        "bentoml.diffusers",
        ("diffusers", "transformers"),
        "Diffusers helper; accelerate is commonly needed at runtime",
    ),
    "onnx": FrameworkCheck("bentoml.onnx", ("onnx", "onnxruntime"), "ONNX helper"),
    "xgboost": FrameworkCheck("bentoml.xgboost", ("xgboost",), "XGBoost helper"),
    "lightgbm": FrameworkCheck("bentoml.lightgbm", ("lightgbm",), "LightGBM helper"),
    "catboost": FrameworkCheck("bentoml.catboost", ("catboost",), "CatBoost helper"),
    "mlflow": FrameworkCheck("bentoml.mlflow", ("mlflow",), "MLflow PyFunc helper"),
    "fastai": FrameworkCheck("bentoml.fastai", ("fastai",), "fastai helper"),
    "flax": FrameworkCheck("bentoml.flax", ("jax", "flax", "tensorflow"), "Flax helper"),
    "easyocr": FrameworkCheck("bentoml.easyocr", ("easyocr",), "EasyOCR helper"),
    "detectron": FrameworkCheck("bentoml.detectron", ("detectron2",), "Detectron helper"),
    "picklable_model": FrameworkCheck(
        "bentoml.picklable_model",
        tuple(),
        "Picklable model helper; still verify project object compatibility",
    ),
}

ALIASES = {
    "torch": "pytorch",
    "pytorch-lightning": "pytorch_lightning",
    "lightning": "pytorch_lightning",
    "picklable": "picklable_model",
    "pickle": "picklable_model",
}


def _find_module(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def _check(name: str) -> dict[str, Any]:
    canonical = ALIASES.get(name, name)
    framework = FRAMEWORKS.get(canonical)
    if framework is None:
        return {
            "framework": name,
            "ok": False,
            "error": f"unknown framework; choose one of: {', '.join(sorted(FRAMEWORKS))}",
        }

    imports = {module: _find_module(module) for module in framework.imports}
    missing = [module for module, present in imports.items() if not present]
    return {
        "framework": canonical,
        "helper": framework.helper,
        "required_imports": imports,
        "missing": missing,
        "ok": not missing,
        "note": framework.note,
        "deprecation_note": (
            "Framework helper modules may be compatibility APIs in modern BentoML and may be exposed through dynamic import routing; "
            "prefer BentoModel/HuggingFaceModel plus explicit framework loading for new services when practical."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check whether optional dependencies for BentoML framework model helpers are importable."
    )
    parser.add_argument(
        "framework",
        nargs="*",
        help="Framework names to check, for example sklearn pytorch transformers onnx. Defaults to all.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero when requested optional dependencies are missing. By default this helper is diagnostic-only.",
    )
    args = parser.parse_args()

    names = args.framework or sorted(FRAMEWORKS)
    results = [_check(name) for name in names]

    if args.json:
        print(json.dumps({"results": results}, indent=2))
    else:
        for result in results:
            status = "OK" if result.get("ok") else "MISSING"
            print(f"{status}: {result['framework']}")
            if "error" in result:
                print(f"  error: {result['error']}")
                continue
            print(f"  helper: {result['helper']}")
            if result.get("required_imports"):
                for module, present in result["required_imports"].items():
                    print(f"  {module}: {'found' if present else 'missing'}")
            else:
                print("  required imports: none beyond BentoML/Python serialization stack")
            if result.get("missing"):
                print(f"  install/declare dependency for: {', '.join(result['missing'])}")
            print(f"  note: {result['note']}")

    return 0 if (not args.strict or all(result.get("ok") for result in results)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
