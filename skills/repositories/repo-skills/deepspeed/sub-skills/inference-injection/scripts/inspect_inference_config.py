#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# DeepSpeed Team
"""Inspect installed DeepSpeed inference configuration fields safely.

This script imports DeepSpeed and prints read-only API facts for
``deepspeed.init_inference`` and ``DeepSpeedInferenceConfig``. It does not
construct models, download artifacts, initialize distributed training, or run
inference.
"""

import argparse
import importlib.util
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Dict


def _field_alias(field: Any) -> Any:
    alias = getattr(field, "alias", None)
    if alias:
        return alias
    return None


def _model_fields(model_cls: Any) -> Dict[str, Dict[str, Any]]:
    fields = getattr(model_cls, "model_fields", None)
    if fields is None:
        fields = getattr(model_cls, "__fields__", {})

    output = {}
    for name, field in fields.items():
        entry = {"alias": _field_alias(field)}
        json_schema_extra = getattr(field, "json_schema_extra", None)
        if json_schema_extra:
            entry["json_schema_extra"] = json_schema_extra
        output[name] = entry
    return output


def _module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _ensure_deepspeed_importable() -> None:
    if importlib.util.find_spec("deepspeed") is not None:
        return

    cwd = Path.cwd()
    if (cwd / "deepspeed" / "__init__.py").is_file():
        sys.path.insert(0, str(cwd))


def main() -> None:
    parser = argparse.ArgumentParser(description="Print installed DeepSpeed inference API facts.")
    parser.add_argument(
        "--check-modules",
        action="store_true",
        help="Also report whether optional inference-related modules can be discovered without importing them.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    args = parser.parse_args()

    _ensure_deepspeed_importable()

    try:
        import deepspeed
        from deepspeed.inference.config import DeepSpeedInferenceConfig
    except ModuleNotFoundError as error:
        missing_name = getattr(error, "name", "a dependency")
        raise SystemExit(
            f"DeepSpeed import failed because {missing_name!r} is not importable. "
            "Install DeepSpeed and its runtime dependencies in the active environment, "
            "or run this script from a checkout root with those dependencies available."
        ) from error

    facts = {
        "deepspeed_version": getattr(deepspeed, "__version__", "unknown"),
        "init_inference_signature": str(inspect.signature(deepspeed.init_inference)),
        "DeepSpeedInferenceConfig_fields": _model_fields(DeepSpeedInferenceConfig),
    }

    if args.check_modules:
        facts["module_availability"] = {
            "transformers": _module_available("transformers"),
            "triton": _module_available("triton"),
            "deepspeed.module_inject": _module_available("deepspeed.module_inject"),
            "deepspeed.inference.v2": _module_available("deepspeed.inference.v2"),
            "deepspeed.inference.quantization": _module_available("deepspeed.inference.quantization"),
        }

    if args.json:
        print(json.dumps(facts, indent=2, sort_keys=True, default=str))
        return

    print(f"DeepSpeed version: {facts['deepspeed_version']}")
    print(f"init_inference signature: {facts['init_inference_signature']}")
    print("DeepSpeedInferenceConfig fields:")
    for name, details in facts["DeepSpeedInferenceConfig_fields"].items():
        alias = details.get("alias")
        if alias:
            print(f"  - {name} (alias: {alias})")
        else:
            print(f"  - {name}")

    if args.check_modules:
        print("Module availability:")
        for module_name, available in facts["module_availability"].items():
            print(f"  - {module_name}: {available}")


if __name__ == "__main__":
    main()
