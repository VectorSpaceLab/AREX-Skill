#!/usr/bin/env python3
"""Safely inspect an AiZynthFinder runtime environment.

The script imports lightweight public modules, checks console scripts, and reports
optional dependency availability. It never starts a retrosynthesis search,
downloads data, opens a database connection, or launches a GUI.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
from typing import Any

CORE_IMPORTS = [
    "aizynthfinder",
    "aizynthfinder.aizynthfinder",
    "aizynthfinder.context.config",
    "aizynthfinder.reactiontree",
]

OPTIONAL_IMPORTS = {
    "rdkit": "chemistry primitives and molecule parsing",
    "onnxruntime": "local ONNX policy model inference",
    "pandas": "batch outputs, stocks, HDF5/JSON tables",
    "tables": "HDF5 stocks and outputs through pandas/PyTables",
    "PIL": "route image rendering",
    "ipywidgets": "notebook/GUI widgets",
    "jupyter": "notebook launcher workflows",
    "molbloom": "molbloom stock files",
    "pymongo": "MongoDB stock backends",
    "route_distances": "route distance and clustering features",
    "tensorflow": "TensorFlow or TensorFlow Serving model paths",
    "grpc": "gRPC remote model serving",
}

CONSOLE_SCRIPTS = [
    "aizynthcli",
    "aizynthapp",
    "cat_aizynth_output",
    "download_public_data",
    "smiles2stock",
]


def import_status(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as error:  # noqa: BLE001 - diagnostic should report import failures clearly.
        return {"ok": False, "error": f"{type(error).__name__}: {error}"}
    version = getattr(module, "__version__", None)
    return {"ok": True, "version": version}


def script_status(script_name: str, run_help: bool) -> dict[str, Any]:
    executable = shutil.which(script_name)
    result: dict[str, Any] = {"found": bool(executable)}
    if not executable or not run_help:
        return result
    try:
        completed = subprocess.run(
            [executable, "--help"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
    except Exception as error:  # noqa: BLE001 - diagnostic should report invocation failures clearly.
        result.update({"help_ok": False, "error": f"{type(error).__name__}: {error}"})
        return result
    result.update(
        {
            "help_ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout_first_line": completed.stdout.splitlines()[0] if completed.stdout.splitlines() else "",
            "stderr_first_line": completed.stderr.splitlines()[0] if completed.stderr.splitlines() else "",
        }
    )
    return result


def build_report(run_cli_help: bool) -> dict[str, Any]:
    try:
        package_version = importlib.metadata.version("aizynthfinder")
    except importlib.metadata.PackageNotFoundError:
        package_version = None

    return {
        "python": {
            "version": sys.version.split()[0],
            "supported_by_repo_metadata": (3, 10) <= sys.version_info[:2] < (3, 13),
        },
        "distribution": {"aizynthfinder": package_version},
        "core_imports": {module_name: import_status(module_name) for module_name in CORE_IMPORTS},
        "optional_imports": {
            module_name: {**import_status(module_name), "purpose": purpose}
            for module_name, purpose in OPTIONAL_IMPORTS.items()
        },
        "console_scripts": {
            script_name: script_status(script_name, run_cli_help) for script_name in CONSOLE_SCRIPTS
        },
    }


def print_human(report: dict[str, Any]) -> None:
    print(f"Python: {report['python']['version']} (supported: {report['python']['supported_by_repo_metadata']})")
    print(f"AiZynthFinder distribution: {report['distribution']['aizynthfinder'] or 'not found'}")
    print("\nCore imports:")
    for module_name, status in report["core_imports"].items():
        marker = "ok" if status["ok"] else "FAIL"
        detail = status.get("version") or status.get("error") or ""
        print(f"  {marker:4} {module_name} {detail}")
    print("\nOptional imports:")
    for module_name, status in report["optional_imports"].items():
        marker = "ok" if status["ok"] else "missing"
        detail = status.get("version") or status.get("error") or status["purpose"]
        print(f"  {marker:7} {module_name}: {detail}")
    print("\nConsole scripts:")
    for script_name, status in report["console_scripts"].items():
        marker = "found" if status["found"] else "missing"
        help_note = ""
        if "help_ok" in status:
            help_note = f" help_ok={status['help_ok']}"
        print(f"  {marker:7} {script_name}{help_note}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect AiZynthFinder imports, optional dependencies, and CLI availability safely.")
    parser.add_argument("--json", action="store_true", help="Print a JSON report instead of a human-readable summary.")
    parser.add_argument("--run-cli-help", action="store_true", help="Run each discovered console script with --help using a short timeout.")
    args = parser.parse_args()

    report = build_report(run_cli_help=args.run_cli_help)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)

    core_ok = all(status["ok"] for status in report["core_imports"].values())
    return 0 if core_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
