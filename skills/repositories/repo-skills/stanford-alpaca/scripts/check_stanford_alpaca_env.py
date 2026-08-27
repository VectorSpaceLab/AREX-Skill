#!/usr/bin/env python3
"""Inspect dependencies for bundled Stanford Alpaca workflows without loading models.

Examples:
  python check_stanford_alpaca_env.py
  python check_stanford_alpaca_env.py --require-cuda
  python check_stanford_alpaca_env.py --json

The command imports optional modules only to report their version and import
status. It never downloads models, reads a dataset, contacts OpenAI, launches
training, or loads checkpoints.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import sys
from typing import Any

MODULES = {
    "torch": "torch",
    "transformers": "transformers",
    "fire": "fire",
    "numpy": "numpy",
    "rouge_score": "rouge-score",
    "openai": "openai",
    "sentencepiece": "sentencepiece",
    "tokenizers": "tokenizers",
}


def version_for(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def parse_major(version: str | None) -> int | None:
    if not version:
        return None
    first = version.split(".", 1)[0]
    return int(first) if first.isdigit() else None


def inspect_modules() -> tuple[dict[str, dict[str, Any]], Any | None]:
    results: dict[str, dict[str, Any]] = {}
    torch_module = None
    for module_name, distribution in MODULES.items():
        version = version_for(distribution)
        try:
            module = importlib.import_module(module_name)
            status = "ok"
            error = None
            if module_name == "torch":
                torch_module = module
        except Exception as exc:  # import errors are the diagnostic result
            status = "error"
            error = f"{type(exc).__name__}: {exc}"
        results[module_name] = {
            "distribution": distribution,
            "version": version,
            "status": status,
            "error": error,
        }
    return results, torch_module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-cuda", action="store_true", help="Return nonzero unless the imported torch exposes CUDA.")
    parser.add_argument("--json", action="store_true", help="Emit a JSON diagnostic document.")
    args = parser.parse_args(argv)

    modules, torch_module = inspect_modules()
    cuda_available = None
    cuda_error = None
    if torch_module is not None:
        try:
            cuda_available = bool(torch_module.cuda.is_available())
        except Exception as exc:
            cuda_error = f"{type(exc).__name__}: {exc}"

    warnings: list[str] = []
    openai_major = parse_major(modules["openai"]["version"])
    if openai_major is not None and openai_major >= 1:
        warnings.append("OpenAI >=1 detected; the historical live generator expects the legacy Completion.create API.")
    numpy_major = parse_major(modules["numpy"]["version"])
    torch_version = modules["torch"]["version"] or ""
    if numpy_major is not None and numpy_major >= 2 and torch_version.startswith("2.0"):
        warnings.append("NumPy >=2 with torch 2.0 can trigger a compiled-extension ABI warning; consider numpy<2 or a matching newer torch.")
    if cuda_available is False:
        warnings.append("CUDA is unavailable to the imported torch; CPU-safe helpers still work, but it does not validate GPU SFT or large recovery.")

    passed = all(item["status"] == "ok" for item in modules.values())
    if args.require_cuda:
        passed = passed and cuda_available is True

    report = {
        "python": sys.version.split()[0],
        "modules": modules,
        "cuda_available": cuda_available,
        "cuda_error": cuda_error,
        "warnings": warnings,
        "passed": passed,
        "require_cuda": args.require_cuda,
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"python: {report['python']}")
        for name, item in modules.items():
            suffix = f" ({item['error']})" if item["error"] else ""
            print(f"{name}: {item['status']} version={item['version']}{suffix}")
        print(f"torch_cuda_available: {cuda_available}")
        for warning in warnings:
            print(f"warning: {warning}")
        print("result: pass" if passed else "result: fail")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
