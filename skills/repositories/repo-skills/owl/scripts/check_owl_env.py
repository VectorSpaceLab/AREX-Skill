#!/usr/bin/env python3
"""Run a safe OWL package/configuration preflight without provider calls."""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, help="optional dotenv-like file; values are never printed")
    parser.add_argument("--check-module", action="store_true", help="also import selected OWL utility modules")
    args = parser.parse_args()
    failures = []
    for distribution in ("owl", "camel-ai"):
        try:
            print(f"{distribution}: {importlib.metadata.version(distribution)}")
        except importlib.metadata.PackageNotFoundError:
            failures.append(f"missing distribution: {distribution}")
    if args.check_module:
        for module in ("owl", "owl.utils.common", "owl.utils.document_toolkit", "owl.utils.gaia", "owl.utils.enhanced_role_playing"):
            try:
                importlib.import_module(module)
                print(f"import {module}: ok")
            except Exception as exc:  # diagnostic output intentionally omits env values
                failures.append(f"import {module}: {type(exc).__name__}: {exc}")
    if args.env_file:
        if not args.env_file.is_file():
            failures.append(f"env file missing: {args.env_file}")
        else:
            names = []
            for raw in args.env_file.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if line and not line.startswith("#") and "=" in line:
                    names.append(line.split("=", 1)[0].strip())
            print(f"env names inspected: {len(names)}")
    print("provider calls: not attempted")
    if failures:
        print("preflight: NOT READY")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("preflight: READY FOR NON-NETWORKED INSPECTION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
