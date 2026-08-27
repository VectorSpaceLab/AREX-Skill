#!/usr/bin/env python3
"""Check public WrenAI imports and CLI availability without contacting a database.

Examples:
  python check_wren_environment.py
  python check_wren_environment.py --require-cli
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import shutil
import subprocess
import sys


DISTRIBUTIONS = ("wrenai", "wren-core-py")
MODULES = ("wren", "wren_core")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-cli",
        action="store_true",
        help="return non-zero when the wren command is not on PATH",
    )
    args = parser.parse_args()

    print(f"Python: {sys.version.split()[0]}")
    failures: list[str] = []
    for distribution in DISTRIBUTIONS:
        try:
            print(f"{distribution}: {importlib.metadata.version(distribution)}")
        except importlib.metadata.PackageNotFoundError:
            failures.append(f"missing distribution: {distribution}")

    for module in MODULES:
        try:
            importlib.import_module(module)
            print(f"import {module}: OK")
        except Exception as exc:  # show an actionable diagnostic, not a traceback
            failures.append(f"cannot import {module}: {type(exc).__name__}: {exc}")

    command = shutil.which("wren")
    if command is None:
        message = "wren CLI: not found on PATH"
        print(message)
        if args.require_cli:
            failures.append(message)
    else:
        result = subprocess.run(
            [command, "--version"], text=True, capture_output=True, timeout=20
        )
        output = (result.stdout or result.stderr).strip()
        print(f"wren CLI: {output or f'exit {result.returncode}'}")
        if result.returncode:
            failures.append("wren --version returned non-zero")

    if failures:
        print("\nFailures:")
        for failure in failures:
            print(f"- {failure}")
        print("Install the smallest needed feature, for example: pip install wrenai")
        return 1
    print("\nWrenAI base environment check passed. No database connection was attempted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
