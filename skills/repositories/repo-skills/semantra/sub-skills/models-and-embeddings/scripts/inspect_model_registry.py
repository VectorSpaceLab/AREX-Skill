#!/usr/bin/env python3
"""Inspect Semantra's model registry without instantiating models.

This helper imports `semantra.models` and prints static registry metadata. It
intentionally does not call any `get_model` factory, so it should not download
Hugging Face models or contact OpenAI.

Examples:
  python inspect_model_registry.py
  python inspect_model_registry.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

MODEL_NAMES = {
    "openai": "text-embedding-ada-002",
    "minilm": "sentence-transformers/all-MiniLM-L6-v2",
    "mpnet": "sentence-transformers/all-mpnet-base-v2",
    "sgpt": "Muennighoff/SGPT-125M-weightedmean-msmarco-specb-bitfit",
    "sgpt-1.3B": "Muennighoff/SGPT-1.3B-weightedmean-msmarco-specb-bitfit",
}


def inspect_registry() -> tuple[int, dict[str, Any]]:
    try:
        from semantra import models as semantra_models
        from semantra import semantra as semantra_cli
    except Exception as exc:  # pragma: no cover - diagnostic path
        return 1, {
            "ok": False,
            "error": repr(exc),
            "recovery": [
                "Install Semantra in the active Python environment.",
                "If the error mentions pkg_resources, install a Setuptools version that still provides pkg_resources (for example setuptools<81) or update Semantra to import importlib.metadata.",
            ],
        }

    presets = {}
    for name, config in semantra_models.models.items():
        presets[name] = {
            "model_name": MODEL_NAMES.get(name),
            "cost_per_token": config.get("cost_per_token"),
            "pool_size": config.get("pool_size"),
            "pool_count": config.get("pool_count"),
            "factory_present": callable(config.get("get_model")),
            "notes": (
                "external OpenAI API; requires OPENAI_API_KEY and compatible OpenAI SDK"
                if name == "openai"
                else "local Hugging Face transformer; first run may download model files"
            ),
        }
    return 0, {
        "ok": True,
        "semantra_version": getattr(semantra_cli, "VERSION", None),
        "transformer_pool_default": getattr(semantra_cli, "TRANSFORMER_POOL_DEFAULT", None),
        "presets": presets,
    }


def print_text(report: dict[str, Any]) -> None:
    if not report.get("ok"):
        print(f"Semantra model registry unavailable: {report.get('error')}")
        for step in report.get("recovery", []):
            print(f"  - {step}")
        return
    print(f"Semantra version: {report.get('semantra_version')}")
    print("Preset models:")
    for name, config in report.get("presets", {}).items():
        print(f"  - {name}")
        print(f"      model: {config.get('model_name')}")
        print(f"      pool_size: {config.get('pool_size')} pool_count: {config.get('pool_count')}")
        print(f"      cost_per_token: {config.get('cost_per_token')}")
        print(f"      notes: {config.get('notes')}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()
    code, report = inspect_registry()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
