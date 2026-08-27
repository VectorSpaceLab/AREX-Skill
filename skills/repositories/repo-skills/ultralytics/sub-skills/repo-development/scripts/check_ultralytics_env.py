#!/usr/bin/env python3
"""Inspect whether the active Python environment can support Ultralytics repo checks."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from importlib import metadata


def package_version(name: str) -> str | None:
    """Return the installed package version, or None when unavailable."""

    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def command_available(name: str) -> bool:
    """Return True when a command is available on PATH."""

    return shutil.which(name) is not None


def import_available(name: str) -> bool:
    """Return True when a module import can be resolved without importing it."""

    return importlib.util.find_spec(name) is not None


def run_help(command: str) -> dict[str, object]:
    """Run a console script help command with a short timeout."""

    executable = shutil.which(command)
    if executable is None:
        return {"available": False, "returncode": None}
    try:
        result = subprocess.run(
            [executable, "--help"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"available": True, "returncode": None, "error": exc.__class__.__name__}
    return {"available": True, "returncode": result.returncode, "stdout_head": result.stdout.splitlines()[:3]}


def collect(run_cli_help: bool) -> dict[str, object]:
    """Collect environment facts useful for selecting repo checks."""

    facts: dict[str, object] = {
        "python_version": sys.version.split()[0],
        "packages": {
            "ultralytics": package_version("ultralytics"),
            "torch": package_version("torch"),
            "torchvision": package_version("torchvision"),
            "pytest": package_version("pytest"),
            "ruff": package_version("ruff"),
            "mkdocs": package_version("mkdocs"),
        },
        "commands": {name: command_available(name) for name in ("yolo", "ultralytics", "pytest", "ruff")},
        "optional_modules": {
            "onnx": import_available("onnx"),
            "onnxruntime": import_available("onnxruntime"),
            "openvino": import_available("openvino"),
            "tensorflow": import_available("tensorflow"),
            "coremltools": import_available("coremltools"),
            "streamlit": import_available("streamlit"),
            "faiss": import_available("faiss"),
            "mlflow": import_available("mlflow"),
            "wandb": import_available("wandb"),
        },
    }
    if run_cli_help:
        facts["cli_help"] = {name: run_help(name) for name in ("yolo", "ultralytics")}
    return facts


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description="Inspect the active environment for safe Ultralytics repo checks.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--run-cli-help", action="store_true", help="Run yolo/ultralytics --help with a short timeout")
    return parser.parse_args()


def main() -> None:
    """Print environment facts."""

    args = parse_args()
    facts = collect(args.run_cli_help)
    if args.json:
        print(json.dumps(facts, indent=2, sort_keys=True))
        return

    print("Ultralytics repo-check environment")
    print(f"Python: {facts['python_version']}")
    print("Packages:")
    for name, version in facts["packages"].items():
        print(f"  - {name}: {version or 'not installed'}")
    print("Commands:")
    for name, available in facts["commands"].items():
        print(f"  - {name}: {'available' if available else 'missing'}")
    print("Optional modules:")
    for name, available in facts["optional_modules"].items():
        print(f"  - {name}: {'available' if available else 'missing'}")


if __name__ == "__main__":
    main()
