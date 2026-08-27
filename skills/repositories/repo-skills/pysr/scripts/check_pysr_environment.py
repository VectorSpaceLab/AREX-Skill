#!/usr/bin/env python3
"""Safe PySR environment probe for agents.

This helper never fits a model. By default it imports PySR to verify the
JuliaCall/SymbolicRegression startup path. Use --skip-import for a metadata-only
probe when first-import Julia setup is not acceptable yet.

Examples:
  python check_pysr_environment.py --skip-import --json
  python check_pysr_environment.py --json --check-cli
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import inspect
import json
import os
import subprocess
import sys
from typing import Any


def dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe a PySR environment without fitting a model.")
    parser.add_argument("--skip-import", action="store_true", help="Only inspect distribution metadata and environment variables.")
    parser.add_argument("--check-cli", action="store_true", help="Run `python -m pysr --help` after import is allowed.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of readable text.")
    args = parser.parse_args()

    result: dict[str, Any] = {
        "python": {"version": sys.version.split()[0], "implementation": sys.implementation.name},
        "packages": {name: dist_version(name) for name in ["pysr", "juliacall", "numpy", "pandas", "scikit-learn", "sympy", "click"]},
        "environment": {key: os.environ.get(key) for key in ["PYTHON_JULIACALL_THREADS", "PYTHON_JULIACALL_HANDLE_SIGNALS", "PYTHON_JULIACALL_OPTLEVEL", "PYSR_AUTOLOAD_EXTENSIONS"]},
        "import": {"status": "skipped" if args.skip_import else "not_started"},
        "cli": {"status": "not_requested"},
    }

    if not args.skip_import:
        try:
            import pysr
            from pysr import PySRRegressor, TemplateExpressionSpec

            result["import"] = {
                "status": "ok",
                "pysr_version": getattr(pysr, "__version__", None),
                "julia_version": str(getattr(pysr.jl, "VERSION", "unknown")),
                "pysrregressor_has_fit": hasattr(PySRRegressor, "fit"),
                "pysrregressor_signature_contains": sorted(k for k in ["niterations", "binary_operators", "operators", "expression_spec", "parallelism", "cluster_manager", "timeout_in_seconds"] if k in inspect.signature(PySRRegressor).parameters),
                "template_spec_available": TemplateExpressionSpec.__name__,
            }
        except Exception as exc:  # pragma: no cover - diagnostic path
            result["import"] = {"status": "error", "type": type(exc).__name__, "message": str(exc)}

    if args.check_cli:
        if args.skip_import:
            result["cli"] = {"status": "skipped", "reason": "--skip-import was supplied"}
        else:
            proc = subprocess.run([sys.executable, "-m", "pysr", "--help"], text=True, capture_output=True, timeout=120)
            result["cli"] = {"status": "ok" if proc.returncode == 0 else "error", "returncode": proc.returncode, "stdout_first_line": (proc.stdout.splitlines() or [""])[0], "stderr_first_line": (proc.stderr.splitlines() or [""])[0]}

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for section, value in result.items():
            print(f"[{section}]")
            print(json.dumps(value, indent=2, sort_keys=True))
    return 0 if result["import"].get("status") in {"ok", "skipped"} and result["cli"].get("status") in {"ok", "not_requested", "skipped"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
