#!/usr/bin/env python3
"""Inspect installed TabPFN public APIs without loading model weights."""

from __future__ import annotations

import argparse
import inspect
import json
from typing import Any

import tabpfn
from tabpfn import TabPFNClassifier, TabPFNRegressor
from tabpfn.constants import ModelVersion
from tabpfn.inference_config import InferenceConfig
from tabpfn.preprocessing.configs import PreprocessorConfig


def summary() -> dict[str, Any]:
    return {
        "tabpfn_version": tabpfn.__version__,
        "model_versions": [m.value for m in ModelVersion],
        "TabPFNClassifier": str(inspect.signature(TabPFNClassifier)),
        "TabPFNRegressor": str(inspect.signature(TabPFNRegressor)),
        "TabPFNClassifier.predict_proba_batched": str(
            inspect.signature(TabPFNClassifier.predict_proba_batched)
        ),
        "TabPFNRegressor.predict_batched": str(
            inspect.signature(TabPFNRegressor.predict_batched)
        ),
        "InferenceConfig_fields": list(InferenceConfig.__dataclass_fields__),
        "PreprocessorConfig": str(inspect.signature(PreprocessorConfig)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()
    data = summary()
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
        return
    for key, value in data.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
