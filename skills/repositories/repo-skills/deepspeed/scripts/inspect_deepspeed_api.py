#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# DeepSpeed Team
"""Inspect DeepSpeed public API signatures and config fields.

The script is read-only and safe for API drift checks. It does not initialize
process groups, launch training, load models, compile ops, or write checkpoints.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
from typing import Any


def field_names(cls: Any) -> list[str]:
    if hasattr(cls, "model_fields"):
        return sorted(cls.model_fields.keys())
    if hasattr(cls, "__fields__"):
        return sorted(cls.__fields__.keys())
    return []


def safe_import(name: str) -> tuple[Any | None, str | None]:
    try:
        return importlib.import_module(name), None
    except Exception as exc:  # pragma: no cover - diagnostic path.
        return None, f"{type(exc).__name__}: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect DeepSpeed API signatures without running workloads.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a readable summary.")
    args = parser.parse_args()

    result: dict[str, Any] = {"ok": True, "errors": []}
    deepspeed, error = safe_import("deepspeed")
    if error:
        result["ok"] = False
        result["errors"].append(f"deepspeed import: {error}")
    else:
        result["deepspeed_version"] = getattr(deepspeed, "__version__", None)
        for attr in ("initialize", "init_inference", "init_distributed"):
            target = getattr(deepspeed, attr, None)
            result[attr] = str(inspect.signature(target)) if target else "missing"

    modules = {
        "DeepSpeedConfig": ("deepspeed.runtime.config", "DeepSpeedConfig"),
        "DeepSpeedZeroConfig": ("deepspeed.runtime.zero.config", "DeepSpeedZeroConfig"),
        "DeepSpeedInferenceConfig": ("deepspeed.inference.config", "DeepSpeedInferenceConfig"),
        "PipelineModule": ("deepspeed.pipe", "PipelineModule"),
        "LayerSpec": ("deepspeed.pipe", "LayerSpec"),
        "TiedLayerSpec": ("deepspeed.pipe", "TiedLayerSpec"),
        "MoE": ("deepspeed.moe.layer", "MoE"),
        "FlopsProfiler": ("deepspeed.profiling.flops_profiler", "FlopsProfiler"),
    }
    result["objects"] = {}
    for label, (module_name, attr) in modules.items():
        module, error = safe_import(module_name)
        if error:
            result["objects"][label] = {"ok": False, "error": error}
            continue
        target = getattr(module, attr, None)
        if target is None:
            result["objects"][label] = {"ok": False, "error": "missing"}
            continue
        item: dict[str, Any] = {"ok": True}
        try:
            item["signature"] = str(inspect.signature(target))
        except Exception:
            item["signature"] = None
        fields = field_names(target)
        if fields:
            item["fields"] = fields
        result["objects"][label] = item

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"DeepSpeed version: {result.get('deepspeed_version', 'unknown')}")
        for key in ("initialize", "init_inference", "init_distributed"):
            if key in result:
                print(f"{key}: {result[key]}")
        for label, item in result["objects"].items():
            print(f"{label}: {item}")
        if result["errors"]:
            print("Errors:")
            for error in result["errors"]:
                print(f"- {error}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
