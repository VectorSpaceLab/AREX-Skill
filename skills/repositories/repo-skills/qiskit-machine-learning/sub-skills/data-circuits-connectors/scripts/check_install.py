#!/usr/bin/env python3
"""Probe the public Qiskit Machine Learning installation and optional extras.

This script intentionally imports only public package names and works from any
current working directory. It is a diagnostic, not an environment installer.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import sys
from typing import Any


PUBLIC_MODULES = (
    "qiskit_machine_learning.datasets",
    "qiskit_machine_learning.circuit.library",
    "qiskit_machine_learning.primitives",
    "qiskit_machine_learning.connectors",
)


def probe(name: str) -> dict[str, Any]:
    """Return availability and import details for one public module/package."""
    result: dict[str, Any] = {"name": name, "found": False, "importable": False}
    try:
        result["found"] = importlib.util.find_spec(name) is not None
    except (ImportError, ModuleNotFoundError, ValueError) as exc:
        result["error"] = f"find_spec: {exc}"
        return result
    if not result["found"]:
        return result
    try:
        module = importlib.import_module(name)
        result["importable"] = True
        result["version"] = getattr(module, "__version__", None)
    except Exception as exc:  # diagnostics must report broken optional imports
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def main(argv: list[str] | None = None) -> int:
    """Run the installation probe."""
    parser = argparse.ArgumentParser(
        description="Check public Qiskit Machine Learning imports and optional extras."
    )
    parser.add_argument(
        "--require-torch",
        action="store_true",
        help="fail unless the PyTorch extra is importable",
    )
    parser.add_argument(
        "--require-sparse",
        action="store_true",
        help="fail unless the sparse extra is importable",
    )
    args = parser.parse_args(argv)

    names = (
        "qiskit_machine_learning",
        "qiskit",
        "numpy",
        "scipy",
        "torch",
        "sparse",
        "matplotlib",
        *PUBLIC_MODULES,
    )
    # Preserve order while avoiding duplicate probes.
    probes = []
    seen: set[str] = set()
    for name in names:
        if name not in seen:
            probes.append(probe(name))
            seen.add(name)

    print("Public installation diagnostics")
    print(f"Python: {sys.executable}")
    for item in probes:
        state = "OK" if item["importable"] else ("found" if item["found"] else "missing")
        suffix = f"; {item['error']}" if "error" in item else ""
        print(f"- {item['name']}: {state}{suffix}")

    by_name = {item["name"]: item for item in probes}
    required = ("qiskit_machine_learning", "qiskit", "numpy", "scipy")
    failures = [name for name in required if not by_name[name]["importable"]]
    if args.require_torch and not by_name["torch"]["importable"]:
        failures.append("torch")
    if args.require_sparse and not by_name["sparse"]["importable"]:
        failures.append("sparse")

    if failures:
        print("Required checks failed: " + ", ".join(failures))
        print("Install the base package with: python -m pip install qiskit-machine-learning")
        if "torch" in failures:
            print("For TorchConnector: python -m pip install 'qiskit-machine-learning[torch]'")
        if "sparse" in failures:
            print("For sparse arrays: python -m pip install 'qiskit-machine-learning[sparse]'")
        return 1

    print("Base package imports are healthy; optional extras are reported above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
