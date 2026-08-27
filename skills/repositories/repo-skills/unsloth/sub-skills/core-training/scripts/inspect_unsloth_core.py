#!/usr/bin/env python3
"""Safely inspect Unsloth Core imports, backend facts, and public signatures.

This script never calls from_pretrained, never downloads models, and never starts
training. It imports Unsloth in a fresh process so import/backend failures can be
captured before a user launches an expensive recipe.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import importlib.util
import inspect
import json
import platform
import sys
from types import ModuleType
from typing import Any


PACKAGES = [
    "unsloth",
    "unsloth_zoo",
    "torch",
    "transformers",
    "trl",
    "peft",
    "bitsandbytes",
    "triton",
    "datasets",
    "sentence_transformers",
    "mlx",
]

SYMBOLS = [
    ("unsloth", "FastLanguageModel.from_pretrained"),
    ("unsloth", "FastLanguageModel.get_peft_model"),
    ("unsloth", "FastLanguageModel.for_inference"),
    ("unsloth", "FastModel.from_pretrained"),
    ("unsloth", "FastModel.get_peft_model"),
    ("unsloth", "FastVisionModel.from_pretrained"),
    ("unsloth", "FastVisionModel.get_peft_model"),
    ("unsloth", "FastTextModel.from_pretrained"),
    ("unsloth", "FastSentenceTransformer.from_pretrained"),
    ("unsloth", "FastSentenceTransformer.get_peft_model"),
    ("unsloth", "is_bfloat16_supported"),
    ("unsloth", "is_bf16_supported"),
    ("unsloth", "UnslothTrainingArguments"),
    ("unsloth", "UnslothTrainer"),
    ("unsloth", "UnslothVisionDataCollator"),
    ("unsloth", "RawTextDataLoader"),
    ("unsloth", "TextPreprocessor"),
    ("unsloth.chat_templates", "get_chat_template"),
    ("unsloth.chat_templates", "standardize_sharegpt"),
]


def package_fact(name: str) -> dict[str, Any]:
    fact: dict[str, Any] = {"available": importlib.util.find_spec(name) is not None}
    try:
        fact["version"] = importlib.metadata.version(name.replace("_", "-"))
    except importlib.metadata.PackageNotFoundError:
        try:
            fact["version"] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            fact["version"] = None
    except Exception as exc:  # metadata can fail for editable/broken installs
        fact["version_error"] = f"{type(exc).__name__}: {exc}"
    return fact


def resolve_attr(module: ModuleType, dotted: str) -> Any:
    current: Any = module
    for part in dotted.split("."):
        current = getattr(current, part)
    return current


def signature_for(obj: Any) -> str | None:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return None


def torch_backend_fact() -> dict[str, Any]:
    fact: dict[str, Any] = {"imported": False}
    try:
        import torch  # type: ignore

        fact["imported"] = True
        fact["version"] = getattr(torch, "__version__", None)
        cuda = getattr(torch, "cuda", None)
        fact["cuda_available"] = bool(cuda and cuda.is_available())
        if fact["cuda_available"]:
            fact["cuda_device_count"] = int(cuda.device_count())
            try:
                major, minor = cuda.get_device_capability()
                fact["cuda_capability"] = f"{major}.{minor}"
            except Exception as exc:
                fact["cuda_capability_error"] = f"{type(exc).__name__}: {exc}"
            try:
                fact["bf16_supported"] = bool(cuda.is_bf16_supported())
            except Exception as exc:
                fact["bf16_error"] = f"{type(exc).__name__}: {exc}"
        xpu = getattr(torch, "xpu", None)
        fact["xpu_available"] = bool(xpu and xpu.is_available())
    except Exception as exc:
        fact["error"] = f"{type(exc).__name__}: {exc}"
    return fact


def inspect_unsloth(import_unsloth: bool) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": True,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": {name: package_fact(name) for name in PACKAGES},
        "torch_backend": torch_backend_fact(),
        "unsloth_import": {"attempted": import_unsloth},
        "symbols": {},
        "warnings": [],
    }

    if not import_unsloth:
        result["warnings"].append("Skipped importing unsloth; signatures were not inspected.")
        return result

    imported: dict[str, ModuleType] = {}
    try:
        imported["unsloth"] = importlib.import_module("unsloth")
        unsloth_module = imported["unsloth"]
        result["unsloth_import"].update(
            {
                "ok": True,
                "version": getattr(unsloth_module, "__version__", None),
                "device_type": getattr(unsloth_module, "DEVICE_TYPE", None),
            }
        )
        try:
            bf16 = getattr(unsloth_module, "is_bfloat16_supported", None) or getattr(
                unsloth_module, "is_bf16_supported", None
            )
            if callable(bf16):
                result["unsloth_import"]["bf16_supported"] = bool(bf16())
        except Exception as exc:
            result["unsloth_import"]["bf16_error"] = f"{type(exc).__name__}: {exc}"
    except Exception as exc:
        result["ok"] = False
        result["unsloth_import"].update({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
        return result

    for module_name, dotted in SYMBOLS:
        key = f"{module_name}.{dotted}"
        try:
            module = imported.get(module_name)
            if module is None:
                module = importlib.import_module(module_name)
                imported[module_name] = module
            obj = resolve_attr(module, dotted)
            result["symbols"][key] = {"present": True, "signature": signature_for(obj)}
        except Exception as exc:
            result["symbols"][key] = {"present": False, "error": f"{type(exc).__name__}: {exc}"}

    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect Unsloth Core imports and public signatures without loading models or training.",
    )
    parser.add_argument(
        "--skip-unsloth-import",
        action="store_true",
        help="Only check package availability and torch backend; do not import unsloth.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output with indentation.",
    )
    args = parser.parse_args(argv)

    result = inspect_unsloth(import_unsloth=not args.skip_unsloth_import)
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
