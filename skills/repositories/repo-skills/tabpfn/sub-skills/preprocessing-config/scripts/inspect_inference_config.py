#!/usr/bin/env python3
"""Print resolved TabPFN inference/preprocessing defaults."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from typing import Any

from tabpfn.constants import ModelVersion
from tabpfn.inference_config import InferenceConfig, cpu_sample_limit
from tabpfn.preprocessing.configs import PreprocessorConfig
from tabpfn.settings import settings


def _serialize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _serialize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(v) for v in value]
    if hasattr(value, 'value') and type(value).__module__ == 'enum':
        return value.value
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=["classifier", "regressor"], default="classifier")
    parser.add_argument("--version", choices=[m.value for m in ModelVersion], default=settings.tabpfn.model_version.value)
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()

    model_version = ModelVersion(args.version)
    if model_version == ModelVersion.V3:
        config = None
        config_source = "checkpoint-embedded"
    else:
        config = InferenceConfig.get_default(
            "multiclass" if args.task == "classifier" else "regression",
            model_version,
        )
        config_source = "static-default"

    payload = {
        "task": args.task,
        "version": args.version,
        "config_source": config_source,
        "cpu_sample_limit": cpu_sample_limit(model_version),
        "settings": {
            "allow_cpu_large_dataset": settings.tabpfn.allow_cpu_large_dataset,
            "mps_memory_fraction": settings.tabpfn.mps_memory_fraction,
            "max_batched_test_rows": settings.tabpfn.max_batched_test_rows,
        },
        "inference_config": asdict(config) if config is not None else None,
        "preprocessor_example": asdict(PreprocessorConfig(name="none")),
        "note": (
            "v3 checkpoints carry the inference config in the checkpoint itself."
            if config is None
            else None
        ),
    }
    if args.json:
        print(json.dumps(_serialize(payload), indent=2, sort_keys=True))
        return
    print(f"task: {args.task}")
    print(f"version: {args.version}")
    print(f"config_source: {config_source}")
    print(f"cpu_sample_limit: {payload['cpu_sample_limit']}")
    if config is None:
        print("inference_config: checkpoint-embedded in v3 checkpoints")
    else:
        print(f"max_cpu_samples: {config.MAX_CPU_SAMPLES}")
        print(f"gpu_preprocessing: {config.ENABLE_GPU_PREPROCESSING}")
        print(f"preprocess_transforms: {len(config.PREPROCESS_TRANSFORMS)}")
    print(f"preprocessor_example: {payload['preprocessor_example']}")


if __name__ == "__main__":
    main()
