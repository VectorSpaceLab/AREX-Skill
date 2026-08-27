#!/usr/bin/env python3
"""Check a fg-data-profiling installation without using repository-local files.

Examples:
  python check_environment.py
  python check_environment.py --json
  python check_environment.py --skip-cli
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from typing import Any


def _run(cmd: list[str], timeout: int = 30) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
        return {
            "command": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except FileNotFoundError:
        return {"command": cmd, "returncode": 127, "stdout": "", "stderr": "command not found"}
    except subprocess.TimeoutExpired as exc:
        return {
            "command": cmd,
            "returncode": 124,
            "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
            "stderr": "timed out",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check fg-data-profiling imports, metadata, and CLI availability.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--skip-cli", action="store_true", help="Do not run CLI --help checks.")
    args = parser.parse_args()

    result: dict[str, Any] = {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "distribution": None,
        "imports": {},
        "entry_points": {},
        "optional_modules": {},
        "cli_checks": [],
        "ok": True,
    }

    try:
        result["distribution"] = metadata.version("fg-data-profiling")
    except metadata.PackageNotFoundError:
        result["ok"] = False
        result["distribution_error"] = "fg-data-profiling distribution metadata not found"

    for module in ["data_profiling", "ydata_profiling"]:
        try:
            imported = importlib.import_module(module)
            result["imports"][module] = {
                "ok": True,
                "version": getattr(imported, "__version__", None),
                "has_ProfileReport": hasattr(imported, "ProfileReport"),
            }
        except Exception as exc:  # noqa: BLE001 - diagnostic surface
            result["ok"] = False
            result["imports"][module] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    for module in ["pyspark", "ipywidgets", "great_expectations", "tangled_up_in_unicode"]:
        result["optional_modules"][module] = importlib.util.find_spec(module) is not None

    for command in ["data_profiling", "pandas_profiling"]:
        path = shutil.which(command)
        result["entry_points"][command] = path is not None
        if path and not args.skip_cli:
            check = _run([command, "--help"], timeout=20)
            result["cli_checks"].append(check)
            if check["returncode"] != 0:
                result["ok"] = False
        elif not path:
            result["entry_points"][command] = False

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Python: {result['python']}")
        print(f"fg-data-profiling distribution: {result.get('distribution') or 'NOT FOUND'}")
        for module, info in result["imports"].items():
            status = "ok" if info.get("ok") else info.get("error")
            print(f"import {module}: {status}")
        for module, present in result["optional_modules"].items():
            print(f"optional {module}: {'present' if present else 'missing'}")
        for command, present in result["entry_points"].items():
            print(f"CLI {command}: {'present' if present else 'missing'}")
        if result["ok"]:
            print("Environment check passed for the selected core package surface.")
        else:
            print("Environment check failed; inspect JSON output for details.")

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
