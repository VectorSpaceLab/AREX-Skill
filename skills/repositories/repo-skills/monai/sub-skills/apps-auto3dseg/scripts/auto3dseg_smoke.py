#!/usr/bin/env python3
"""Safe MONAI Auto3DSeg inspection smoke script.

This script checks installed MONAI application APIs without training, reading
medical images, downloading datasets/templates, or requiring a source checkout.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import subprocess
import sys
from typing import Any


AUTO3DSEG_OBJECTS = [
    ("monai.apps.auto3dseg", "AutoRunner"),
    ("monai.apps.auto3dseg", "DataAnalyzer"),
    ("monai.apps.auto3dseg", "BundleGen"),
    ("monai.apps.auto3dseg", "EnsembleRunner"),
    ("monai.apps.auto3dseg", "NNIGen"),
    ("monai.apps.auto3dseg", "OptunaGen"),
    ("monai.apps.nnunet", "nnUNetV2Runner"),
    ("monai.apps", "MedNISTDataset"),
    ("monai.apps", "DecathlonDataset"),
]

OPTIONAL_MODULES = ["fire", "nni", "optuna", "nnunetv2", "batchgenerators", "nibabel", "tqdm"]


def import_status(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as error:  # noqa: BLE001
        return {"ok": False, "error": f"{type(error).__name__}: {error}"}
    return {"ok": True, "version": getattr(module, "__version__", None)}


def object_signature(module_name: str, object_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
        obj = getattr(module, object_name)
        signature = str(inspect.signature(obj))
    except Exception as error:  # noqa: BLE001
        return {"ok": False, "error": f"{type(error).__name__}: {error}"}
    return {"ok": True, "signature": signature}


def run_help(module_name: str, timeout: int) -> dict[str, Any]:
    command = [sys.executable, "-m", module_name, "--", "--help"]
    try:
        completed = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
    except Exception as error:  # noqa: BLE001
        return {"ok": False, "command": command, "error": f"{type(error).__name__}: {error}"}
    output_lines = completed.stdout.splitlines()
    return {
        "ok": completed.returncode == 0,
        "command": command,
        "returncode": completed.returncode,
        "first_lines": output_lines[:80],
    }


def build_report(include_help: bool, help_timeout: int) -> dict[str, Any]:
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "imports": {
            "monai": import_status("monai"),
            "monai.apps.auto3dseg": import_status("monai.apps.auto3dseg"),
            "monai.auto3dseg": import_status("monai.auto3dseg"),
            "monai.apps.nnunet": import_status("monai.apps.nnunet"),
        },
        "optional_modules": {name: import_status(name) for name in OPTIONAL_MODULES},
        "signatures": {
            f"{module_name}.{object_name}": object_signature(module_name, object_name)
            for module_name, object_name in AUTO3DSEG_OBJECTS
        },
        "notes": [
            "No AutoRunner.run(), DataAnalyzer.get_all_case_stats(), BundleGen.generate(), HPO, downloads, or training were executed.",
            "CLI help requires the optional fire package; nnU-Net execution requires external nnU-Net dependencies and data layout.",
        ],
    }
    if include_help:
        report["cli_help"] = {
            "monai.apps.auto3dseg": run_help("monai.apps.auto3dseg", help_timeout),
            "monai.apps.nnunet": run_help("monai.apps.nnunet", help_timeout),
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely inspect installed MONAI Auto3DSeg app APIs.")
    parser.add_argument("--json", action="store_true", help="Emit compact JSON instead of a readable summary.")
    parser.add_argument("--include-help", action="store_true", help="Also run Fire CLI --help for app routers.")
    parser.add_argument("--help-timeout", type=int, default=20, help="Seconds before CLI help inspection times out.")
    args = parser.parse_args()

    report = build_report(include_help=args.include_help, help_timeout=args.help_timeout)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    print("MONAI Auto3DSeg safe inspection")
    print("================================")
    for name, status in report["imports"].items():
        suffix = f" version={status['version']}" if status.get("version") else ""
        print(f"import {name}: {'ok' if status['ok'] else 'failed'}{suffix}")
        if not status["ok"]:
            print(f"  {status['error']}")

    print("\nOptional modules")
    for name, status in report["optional_modules"].items():
        suffix = f" version={status['version']}" if status.get("version") else ""
        print(f"{name}: {'present' if status['ok'] else 'missing'}{suffix}")

    print("\nSignatures")
    for name, status in report["signatures"].items():
        if status["ok"]:
            print(f"{name}{status['signature']}")
        else:
            print(f"{name}: failed ({status['error']})")

    if args.include_help:
        print("\nCLI help")
        for name, status in report["cli_help"].items():
            print(f"{name}: returncode={status.get('returncode')} ok={status['ok']}")
            for line in status.get("first_lines", [])[:12]:
                print(f"  {line}")
            if not status["ok"] and "error" in status:
                print(f"  {status['error']}")

    print("\nNo training, image analysis, HPO, downloads, or nnU-Net execution were run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
