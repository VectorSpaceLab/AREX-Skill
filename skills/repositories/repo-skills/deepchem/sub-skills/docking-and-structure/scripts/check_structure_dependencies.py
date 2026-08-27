#!/usr/bin/env python3
"""Report DeepChem structure-workflow dependencies without running docking."""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import shutil
import subprocess
import sys
from typing import Any, Dict, Iterable, Optional


PYTHON_IMPORTS = [
    ("deepchem", "DeepChem package"),
    ("rdkit", "RDKit molecule parsing"),
    ("mdtraj", "binding pocket features and neighbor lists"),
    ("vina", "AutoDock Vina Python API"),
    ("pdbfixer", "PDB cleanup for prepare_inputs"),
    ("openmm", "OpenMM/PDBFixer support"),
    ("pymatgen", "materials structures/compositions"),
    ("matminer", "materials property featurizers"),
    ("networkx", "LCNN material graph helpers"),
    ("scipy", "scientific/material helpers"),
    ("torch", "DFT and torch model surfaces"),
    ("dqc", "DFT quantum chemistry backend"),
    ("tensorflow", "optional model backend"),
    ("jax", "optional model backend"),
]

COMMANDS = [
    ("vina", ["vina", "--help"]),
    ("gnina", ["gnina", "--help"]),
]


def import_status(module_name: str, purpose: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "module": module_name,
        "purpose": purpose,
        "available": False,
        "version": None,
        "error": None,
    }
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic helper should report all import failures.
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result

    result["available"] = True
    version = getattr(module, "__version__", None)
    if version is not None:
        result["version"] = str(version)
    return result


def command_status(name: str, command: Iterable[str], run_help: bool) -> Dict[str, Any]:
    executable = shutil.which(name)
    result: Dict[str, Any] = {
        "command": name,
        "available_on_path": executable is not None,
        "path": executable,
        "help_ran": False,
        "returncode": None,
        "first_output_line": None,
        "error": None,
    }
    if executable is None or not run_help:
        return result

    try:
        completed = subprocess.run(
            list(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001 - diagnostic helper should report all execution failures.
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result

    result["help_ran"] = True
    result["returncode"] = completed.returncode
    for line in completed.stdout.splitlines():
        stripped = line.strip()
        if stripped:
            result["first_output_line"] = stripped[:240]
            break
    return result


def summarize(report: Dict[str, Any]) -> Dict[str, str]:
    imports = {item["module"]: item for item in report["python_imports"]}
    commands = {item["command"]: item for item in report["external_commands"]}

    def ok_import(name: str) -> bool:
        return bool(imports.get(name, {}).get("available"))

    def ok_command(name: str) -> bool:
        return bool(commands.get(name, {}).get("available_on_path"))

    return {
        "pocket_finding": "ready if protein files parse with DeepChem/RDKit"
        if ok_import("deepchem") and ok_import("rdkit") else "blocked: needs DeepChem and RDKit parsing stack",
        "binding_pocket_features": "ready" if ok_import("mdtraj") else "blocked: needs mdtraj",
        "vina_docking": "ready for smoke test" if ok_import("vina") else "blocked: needs Python vina package",
        "gnina_docking": "binary visible; still confirm Linux/CUDA/input formats"
        if ok_command("gnina") else "blocked or unchecked: gnina command not on PATH",
        "input_preparation": "ready" if ok_import("rdkit") and ok_import("pdbfixer") and ok_import("openmm") else "blocked: needs RDKit, pdbfixer, and openmm",
        "materials": "ready for many material featurizers" if ok_import("pymatgen") and ok_import("matminer") else "partial/blocked: check pymatgen and matminer",
        "dft": "ready for DFT import smoke tests" if ok_import("torch") and ok_import("dqc") else "blocked: needs torch and likely dqc",
    }


def print_text(report: Dict[str, Any]) -> None:
    print("DeepChem structure dependency report")
    print(f"Python: {report['python']}")
    print(f"Platform: {report['platform']}")
    print("")
    print("Python imports:")
    for item in report["python_imports"]:
        status = "OK" if item["available"] else "MISSING"
        version = f" ({item['version']})" if item["version"] else ""
        detail = item["error"] or item["purpose"]
        print(f"  [{status}] {item['module']}{version}: {detail}")
    print("")
    print("External commands:")
    for item in report["external_commands"]:
        status = "OK" if item["available_on_path"] else "MISSING"
        path = item["path"] or "not found"
        extra = ""
        if item["help_ran"]:
            extra = f"; help returncode={item['returncode']}"
            if item["first_output_line"]:
                extra += f"; first line={item['first_output_line']}"
        if item["error"]:
            extra += f"; error={item['error']}"
        print(f"  [{status}] {item['command']}: {path}{extra}")
    print("")
    print("Workflow summary:")
    for name, status in report["workflow_summary"].items():
        print(f"  - {name}: {status}")


def build_report(run_help: bool) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "python": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "python_imports": [import_status(module, purpose) for module, purpose in PYTHON_IMPORTS],
        "external_commands": [command_status(name, command, run_help) for name, command in COMMANDS],
    }
    report["workflow_summary"] = summarize(report)
    return report


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check optional dependencies for DeepChem docking, complex featurization, materials, and DFT workflows."
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--run-help",
        action="store_true",
        help="Run '<binary> --help' for discovered vina/gnina commands. By default only PATH lookup is performed.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    report = build_report(run_help=args.run_help)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
