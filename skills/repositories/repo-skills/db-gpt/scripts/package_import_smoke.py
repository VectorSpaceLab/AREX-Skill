#!/usr/bin/env python3
"""Read-only DB-GPT package/version smoke check.

Usage:
    python package_import_smoke.py
    python package_import_smoke.py --json

This helper imports only selected public modules and never starts a service,
contacts a provider, resolves credentials, downloads a model, or opens a
user database.
"""
from __future__ import annotations

import argparse
import importlib
import json
from importlib.metadata import PackageNotFoundError, version

DISTRIBUTIONS = (
    "dbgpt",
    "dbgpt-app",
    "dbgpt-client",
    "dbgpt-ext",
    "dbgpt-serve",
    "dbgpt-sandbox",
)
MODULES = (
    "dbgpt",
    "dbgpt_app",
    "dbgpt_client",
    "dbgpt_ext",
    "dbgpt_serve",
    "dbgpt_sandbox",
)


def collect() -> dict[str, object]:
    distributions: dict[str, str | None] = {}
    for name in DISTRIBUTIONS:
        try:
            distributions[name] = version(name)
        except PackageNotFoundError:
            distributions[name] = None

    imports: dict[str, str] = {}
    failures: dict[str, str] = {}
    for name in MODULES:
        try:
            module = importlib.import_module(name)
            imports[name] = getattr(module, "__version__", "imported")
        except Exception as exc:  # pragma: no cover - reports environment facts
            failures[name] = f"{type(exc).__name__}: {exc}"

    return {"distributions": distributions, "imports": imports, "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args()
    report = collect()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for name, value in report["distributions"].items():
            print(f"distribution {name}: {value or 'missing'}")
        for name in report["imports"]:
            print(f"import {name}: ok")
        for name, error in report["failures"].items():
            print(f"import {name}: {error}")
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
