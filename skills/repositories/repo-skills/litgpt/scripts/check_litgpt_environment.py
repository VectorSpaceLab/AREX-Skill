#!/usr/bin/env python3
"""Safely inspect a Python environment for LitGPT workflow readiness.

This helper imports package metadata and optional dependencies only. It does not
load model weights, download files, train, evaluate, convert checkpoints, or
start servers.

Examples:
    python scripts/check_litgpt_environment.py
    python scripts/check_litgpt_environment.py --json
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import sys
from dataclasses import asdict, dataclass
from typing import Iterable


OPTIONAL_IMPORTS = {
    "requests": "LitGPT CLI startup with jsonargparse URL config mode",
    "bitsandbytes": "bnb.* quantized inference/training/serving",
    "lm_eval": "litgpt evaluate and LM Evaluation Harness tasks",
    "litserve": "litgpt serve HTTP APIs",
    "jinja2": "OpenAI-compatible serving chat templates",
    "litdata": "large pretraining/data module workflows",
    "tensorboard": "tensorboard training logger",
    "wandb": "Weights & Biases training logger",
    "mlflow": "MLflow training logger",
    "litlogger": "Lightning AI LitLogger training logger",
    "transformers": "some checkpoint/tokenizer conversion and comparison workflows",
    "datasets": "evaluation and dataset preparation workflows",
    "sentencepiece": "some model tokenizers",
}

CORE_IMPORTS = ("litgpt", "torch", "lightning", "jsonargparse", "huggingface_hub", "safetensors", "tokenizers")


@dataclass
class ImportStatus:
    name: str
    available: bool
    version: str | None = None
    purpose: str | None = None
    error: str | None = None


def package_version(name: str) -> str | None:
    candidates = [name, name.replace("_", "-"), name.replace("-", "_")]
    for candidate in candidates:
        try:
            return metadata.version(candidate)
        except metadata.PackageNotFoundError:
            continue
    return None


def check_import(name: str, purpose: str | None = None) -> ImportStatus:
    try:
        importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - diagnostic helper should report import failures
        return ImportStatus(name=name, available=False, purpose=purpose, error=f"{type(exc).__name__}: {exc}")
    return ImportStatus(name=name, available=True, version=package_version(name), purpose=purpose)


def command_available(command: str) -> bool:
    if shutil.which(command) is not None:
        return True
    try:
        entry_points = metadata.entry_points()
        scripts = entry_points.select(group="console_scripts") if hasattr(entry_points, "select") else entry_points.get("console_scripts", [])
        return any(entry_point.name == command for entry_point in scripts)
    except Exception:
        return False


def build_report(include_optional: Iterable[str]) -> dict:
    core = [asdict(check_import(name)) for name in CORE_IMPORTS]
    optional = [asdict(check_import(name, OPTIONAL_IMPORTS[name])) for name in include_optional]

    console_scripts = {
        "litgpt": command_available("litgpt"),
    }

    torch_backend = None
    try:
        import torch

        torch_backend = {
            "version": getattr(torch, "__version__", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            "mps_available": bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available()),
        }
    except Exception as exc:  # noqa: BLE001
        torch_backend = {"error": f"{type(exc).__name__}: {exc}"}

    return {
        "python": sys.version.split()[0],
        "core_imports": core,
        "optional_imports": optional,
        "console_scripts": console_scripts,
        "torch_backend": torch_backend,
        "status": "ok" if all(item["available"] for item in core) else "missing-core",
        "notes": [
            "Optional dependencies are workflow-specific; missing optional packages are not failures unless the selected task needs them.",
            "This helper does not prove model weights, checkpoint layout, CUDA kernels, training, evaluation, or server startup work.",
        ],
    }


def print_text(report: dict) -> None:
    print(f"Python: {report['python']}")
    print(f"Status: {report['status']}")
    print("\nCore imports:")
    for item in report["core_imports"]:
        marker = "OK" if item["available"] else "MISSING"
        suffix = f" {item['version']}" if item.get("version") else ""
        print(f"  [{marker}] {item['name']}{suffix}")
        if item.get("error"):
            print(f"      {item['error']}")
    print("\nOptional imports:")
    for item in report["optional_imports"]:
        marker = "OK" if item["available"] else "missing"
        suffix = f" {item['version']}" if item.get("version") else ""
        print(f"  [{marker}] {item['name']}{suffix} - {item['purpose']}")
        if item.get("error"):
            print(f"      {item['error']}")
    print("\nConsole scripts:")
    for name, present in report["console_scripts"].items():
        print(f"  [{'OK' if present else 'missing'}] {name}")
    print("\nTorch backend:")
    print(json.dumps(report["torch_backend"], indent=2, sort_keys=True))
    print("\nNotes:")
    for note in report["notes"]:
        print(f"  - {note}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely inspect LitGPT environment readiness.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--optional",
        action="append",
        choices=sorted(OPTIONAL_IMPORTS),
        help="Limit optional checks to selected import names. Can be repeated.",
    )
    args = parser.parse_args(argv)

    optional = args.optional if args.optional else sorted(OPTIONAL_IMPORTS)
    report = build_report(optional)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
