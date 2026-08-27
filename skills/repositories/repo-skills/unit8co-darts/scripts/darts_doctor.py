#!/usr/bin/env python3
"""Darts package import and optional dependency doctor."""
from __future__ import annotations

import argparse
import importlib.util
import json


def run() -> dict:
    import darts
    from darts import TimeSeries
    from darts.models import ExponentialSmoothing, NaiveSeasonal

    optional = {}
    for name in [
        "torch",
        "pytorch_lightning",
        "shap",
        "prophet",
        "lightgbm",
        "xgboost",
        "catboost",
        "statsforecast",
        "neuralforecast",
        "tirex",
        "onnxruntime",
        "optuna",
        "ray",
        "polars",
    ]:
        optional[name] = bool(importlib.util.find_spec(name))

    return {
        "status": "ok",
        "darts_version": getattr(darts, "__version__", "unknown"),
        "public_api": {
            "TimeSeries": str(TimeSeries),
            "NaiveSeasonal": str(NaiveSeasonal),
            "ExponentialSmoothing": str(ExponentialSmoothing),
        },
        "optional_dependencies": optional,
        "notes": [
            "CPU import checks do not prove CUDA/GPU/TPU execution.",
            "Foundation wrappers may require local weights/cache or approved network downloads.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print JSON result")
    args = parser.parse_args()
    result = run()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Darts doctor: {result['status']} (version {result['darts_version']})")
        for name, available in result["optional_dependencies"].items():
            print(f"{name}: {'available' if available else 'missing'}")
        for note in result["notes"]:
            print(f"note: {note}")


if __name__ == "__main__":
    main()
