#!/usr/bin/env python3
"""Check Accelerate import, CLI, and optional backend availability safely.

Example:
    python check_accelerate_environment.py --json

This script does not launch distributed jobs, download models, contact tracker
services, or require the original Accelerate repository checkout.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


OPTIONAL_MODULES = {
    "deepspeed": "DeepSpeed ZeRO workflows",
    "torch_xla": "TPU/XLA workflows",
    "transformer_engine": "Transformer Engine FP8 workflows",
    "torchao": "torchao FP8/quantization workflows",
    "bitsandbytes": "bitsandbytes quantization workflows",
    "wandb": "Weights & Biases tracking",
    "tensorboard": "TensorBoard tracking",
}


def import_status(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as error:  # noqa: BLE001 - diagnostic should capture import failures
        return {"ok": False, "error": f"{type(error).__name__}: {error}"}
    version = getattr(module, "__version__", None)
    return {"ok": True, "version": version}


def run_cli_help(command: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=20)
    except FileNotFoundError:
        return {"ok": False, "error": "command not found"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "help command timed out"}
    first_line = result.stdout.splitlines()[0] if result.stdout.splitlines() else ""
    return {"ok": result.returncode == 0, "returncode": result.returncode, "first_line": first_line}


def collect() -> dict[str, Any]:
    report: dict[str, Any] = {"python": sys.version.split()[0]}
    report["accelerate"] = import_status("accelerate")
    try:
        report["accelerate"]["distribution_version"] = metadata.version("accelerate")
    except metadata.PackageNotFoundError:
        report["accelerate"]["distribution_version"] = None

    report["torch"] = import_status("torch")
    if report["torch"]["ok"]:
        import torch

        report["torch"]["cuda_available"] = bool(torch.cuda.is_available())
        report["torch"]["cuda_device_count"] = int(torch.cuda.device_count())

    executable = shutil.which("accelerate")
    if executable is None:
        sibling_executable = Path(sys.executable).with_name("accelerate")
        if sibling_executable.exists():
            executable = str(sibling_executable)
    command = [executable, "--help"] if executable else [sys.executable, "-m", "accelerate.commands.accelerate_cli", "--help"]
    report["cli"] = {
        "accelerate_path": executable,
        "accelerate_help": run_cli_help(command),
    }
    report["optional_modules"] = {
        name: {"purpose": purpose, **import_status(name)} for name, purpose in OPTIONAL_MODULES.items()
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely check Accelerate imports, CLI help, and optional modules.")
    parser.add_argument("--json", action="store_true", help="Print the full report as JSON.")
    args = parser.parse_args()

    report = collect()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        accelerate = report["accelerate"]
        torch = report["torch"]
        print(f"accelerate import: {accelerate['ok']} version={accelerate.get('distribution_version')}")
        print(f"torch import: {torch['ok']} version={torch.get('version')} cuda={torch.get('cuda_available')}")
        print(f"accelerate CLI: {report['cli']['accelerate_help']['ok']} path={report['cli']['accelerate_path']}")
        missing = [name for name, status in report["optional_modules"].items() if not status["ok"]]
        print("missing optional modules: " + (", ".join(missing) if missing else "none"))
    return 0 if report["accelerate"]["ok"] and report["torch"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
