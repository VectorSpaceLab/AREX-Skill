#!/usr/bin/env python3
"""Print a safe summary of the active TabPFN environment.

This helper imports the installed package, reports key versions and settings,
and does not download model weights.
"""

from __future__ import annotations

import argparse
import json
import inspect
from dataclasses import asdict, is_dataclass
from typing import Any

import tabpfn
import torch

from tabpfn import TabPFNClassifier, TabPFNRegressor
from tabpfn.constants import ModelVersion
from tabpfn.inference_config import InferenceConfig
from tabpfn.preprocessing.configs import PreprocessorConfig
from tabpfn.settings import settings


def _serialize(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _serialize(val) for key, val in value.items()}
    if is_dataclass(value):
        return _serialize(asdict(value))
    if hasattr(value, "value") and type(value).__module__ == "enum":
        return value.value
    return str(value)


def build_summary() -> dict[str, Any]:
    return {
        "tabpfn_version": tabpfn.__version__,
        "model_versions": [member.value for member in ModelVersion],
        "classifier_signature": str(inspect.signature(TabPFNClassifier)),
        "regressor_signature": str(inspect.signature(TabPFNRegressor)),
        "inference_config_fields": list(InferenceConfig.__dataclass_fields__),
        "preprocessor_config_signature": str(inspect.signature(PreprocessorConfig)),
        "settings": {
            "model_cache_dir": str(settings.tabpfn.model_cache_dir)
            if settings.tabpfn.model_cache_dir is not None
            else None,
            "model_version": settings.tabpfn.model_version.value,
            "allow_cpu_large_dataset": settings.tabpfn.allow_cpu_large_dataset,
            "mps_memory_fraction": settings.tabpfn.mps_memory_fraction,
            "max_batched_test_rows": settings.tabpfn.max_batched_test_rows,
        },
        "torch": {
            "version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "mps_available": torch.backends.mps.is_available(),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print a safe summary of the installed TabPFN environment."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args()

    summary = build_summary()
    if args.json:
        print(json.dumps(_serialize(summary), indent=2, sort_keys=True))
        return

    print(f"tabpfn: {summary['tabpfn_version']}")
    print(f"model versions: {', '.join(summary['model_versions'])}")
    print(f"cuda available: {summary['torch']['cuda_available']}")
    print(f"mps available: {summary['torch']['mps_available']}")
    print(f"default model version: {summary['settings']['model_version']}")
    print(f"cache dir: {summary['settings']['model_cache_dir']}")
    print(f"allow_cpu_large_dataset: {summary['settings']['allow_cpu_large_dataset']}")
    print(f"mps_memory_fraction: {summary['settings']['mps_memory_fraction']}")
    print(f"max_batched_test_rows: {summary['settings']['max_batched_test_rows']}")


if __name__ == "__main__":
    main()
