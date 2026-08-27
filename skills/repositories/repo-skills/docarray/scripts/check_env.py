#!/usr/bin/env python3
"""Check DocArray imports and selected optional surfaces without side effects.

The checker never starts a service, downloads data, or mutates an environment.
It reports missing optional packages as actionable diagnostics instead of raw
tracebacks and can run from any current working directory.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import sys
from typing import Optional


def probe(module: str) -> tuple[bool, str]:
    try:
        imported = importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - diagnostics must show backend failure
        return False, f"missing/unusable: {exc}"
    return True, getattr(imported, "__version__", "imported")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--optional", action="store_true", help="Probe optional proto/pandas/web/tensor modules too.")
    args = parser.parse_args(argv)

    try:
        distribution = importlib.metadata.version("docarray")
    except importlib.metadata.PackageNotFoundError:
        print("FAIL: distribution docarray is not installed")
        return 1

    ok, detail = probe("docarray")
    print(f"docarray distribution={distribution}")
    print(f"docarray import={'OK' if ok else 'FAIL'} ({detail})")
    if not ok:
        return 1

    modules = ["numpy", "pydantic", "orjson"]
    if args.optional:
        modules += ["google.protobuf", "pandas", "fastapi", "torch", "tensorflow", "jax", "hnswlib"]
    failed_required = False
    for module in modules:
        present, value = probe(module)
        print(f"{module}={'OK' if present else 'MISSING'} ({value})")
        if module in {"numpy", "pydantic", "orjson"} and not present:
            failed_required = True

    try:
        from docarray import BaseDoc, DocList, DocVec  # noqa: F401
        from docarray.index import InMemoryExactNNIndex  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: core DocArray API import: {exc}")
        return 1
    print("core API import=OK")
    return 1 if failed_required else 0


if __name__ == "__main__":
    raise SystemExit(main())
