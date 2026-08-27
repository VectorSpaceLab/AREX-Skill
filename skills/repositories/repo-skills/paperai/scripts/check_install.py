#!/usr/bin/env python3
"""No-download import and distribution check for the paperai runtime."""

from __future__ import annotations

import importlib
import importlib.metadata
import sys


MODULES = (
    "paperai",
    "paperai.index",
    "paperai.query",
    "paperai.export",
    "paperai.report.execute",
)


def main() -> int:
    failures: list[str] = []
    try:
        print(f"paperai distribution: {importlib.metadata.version('paperai')}")
    except importlib.metadata.PackageNotFoundError:
        failures.append("distribution 'paperai' is not installed")

    for name in MODULES:
        try:
            importlib.import_module(name)
            print(f"OK import {name}")
        except Exception as error:  # noqa: BLE001 - report every import failure.
            failures.append(f"{name}: {type(error).__name__}: {error}")

    if failures:
        print("Import check failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Import check passed; no model or corpus was loaded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
