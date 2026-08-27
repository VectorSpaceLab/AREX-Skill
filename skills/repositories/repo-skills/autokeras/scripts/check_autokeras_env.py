#!/usr/bin/env python3
"""Check AutoKeras importability, Keras backend, and public API visibility.

Examples:
  python check_autokeras_env.py --backend torch
  python check_autokeras_env.py --backend torch --show-signatures
This script performs no training and downloads no data.
"""
from __future__ import annotations
import argparse, importlib, inspect, os, sys
PUBLIC = ["AutoModel", "ImageClassifier", "ImageRegressor", "TextClassifier", "TextRegressor", "StructuredDataClassifier", "StructuredDataRegressor", "ImageInput", "TextInput", "StructuredDataInput", "Input", "ClassificationHead", "RegressionHead", "ImageBlock", "TextBlock", "StructuredDataBlock", "DenseBlock", "ConvBlock", "Merge", "Greedy", "RandomSearch", "Hyperband", "BayesianOptimization"]
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", default=None, help="Set KERAS_BACKEND before importing Keras/AutoKeras, e.g. torch.")
    parser.add_argument("--show-signatures", action="store_true")
    args = parser.parse_args()
    if args.backend:
        os.environ["KERAS_BACKEND"] = args.backend
    try:
        import keras
        import autokeras as ak
    except Exception as exc:
        print(f"IMPORT_ERROR {type(exc).__name__}: {exc}", file=sys.stderr)
        print("Set KERAS_BACKEND before import and install autokeras plus a Keras backend.", file=sys.stderr)
        return 2
    print(f"autokeras_version={getattr(ak, '__version__', 'unknown')}")
    print(f"keras_version={getattr(keras, '__version__', 'unknown')}")
    try:
        print(f"keras_backend={keras.backend.backend()}")
    except Exception as exc:
        print(f"keras_backend_error={type(exc).__name__}: {exc}")
    missing = [name for name in PUBLIC if not hasattr(ak, name)]
    print(f"public_api_missing={missing}")
    for mod in ["torch", "tensorflow", "jax"]:
        try:
            imported = importlib.import_module(mod)
            print(f"optional_backend_{mod}=available version={getattr(imported, '__version__', 'unknown')}")
        except Exception as exc:
            print(f"optional_backend_{mod}=unavailable {type(exc).__name__}: {exc}")
    if args.show_signatures:
        for name in PUBLIC:
            if hasattr(ak, name):
                try:
                    print(f"{name}{inspect.signature(getattr(ak, name))}")
                except Exception as exc:
                    print(f"{name} signature unavailable: {exc}")
    return 1 if missing else 0
if __name__ == "__main__":
    raise SystemExit(main())
