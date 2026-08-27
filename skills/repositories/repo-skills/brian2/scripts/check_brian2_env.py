#!/usr/bin/env python3
"""Read-only Brian2 environment diagnostic.

Run from any working directory with the target environment's Python. The
report intentionally prints package/runtime facts, not executable or checkout
paths. It never installs packages, changes preferences, compiles code, or
writes files.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import platform
import shutil
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Brian2 import and optional runtime prerequisites")
    parser.add_argument("--json", action="store_true", help="emit a compact JSON report")
    args = parser.parse_args()

    report: dict[str, object] = {
        "python": platform.python_version(),
        "python_supported": sys.version_info >= (3, 12),
        "platform": platform.platform(aliased=True),
        "compiler": shutil.which("g++") or shutil.which("c++") or shutil.which("cl"),
        "gsl_config": bool(shutil.which("gsl-config")),
    }
    try:
        report["distribution_version"] = importlib.metadata.version("Brian2")
    except importlib.metadata.PackageNotFoundError:
        report["distribution_version"] = None
    try:
        brian2 = importlib.import_module("brian2")
        report["import"] = "passed"
        report["module_version"] = getattr(brian2, "__version__", None)
        report["codegen_target"] = str(brian2.prefs.codegen.target)
        report["required_imports"] = {
            name: importlib.import_module(name).__name__
            for name in ("numpy", "sympy", "pyparsing", "jinja2")
        }
    except Exception as exc:  # diagnostic output should name the class, not leak paths
        report["import"] = f"failed: {type(exc).__name__}: {exc}"

    if args.json:
        import json

        print(json.dumps(report, sort_keys=True))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")

    return 0 if report.get("import") == "passed" and report["python_supported"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
