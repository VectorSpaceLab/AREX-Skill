#!/usr/bin/env python3
"""Inspect public wren_core binding capabilities without a repository checkout.

Usage:
  python inspect_wren_core.py
"""
from __future__ import annotations

import importlib.metadata
import inspect


def main() -> int:
    try:
        import wren_core
        from wren_core import SessionContext
    except Exception as exc:
        print(f"Cannot import wren_core: {type(exc).__name__}: {exc}")
        return 1
    try:
        print(f"wren-core-py: {importlib.metadata.version('wren-core-py')}")
    except importlib.metadata.PackageNotFoundError:
        print("wren-core-py distribution metadata: unavailable")
    print(f"SessionContext signature: {inspect.signature(SessionContext)}")
    methods = [
        "transform_sql", "query", "dry_run", "register_csv", "register_parquet",
        "load_mdl", "list_tables", "get_available_functions", "pushdown_limit",
    ]
    print("Available methods:")
    for method in methods:
        print(f"- {method}: {'yes' if hasattr(SessionContext, method) else 'no'}")
    helpers = ["to_json_base64", "to_manifest", "cube_query_to_sql"]
    print("Helpers:")
    for helper in helpers:
        print(f"- {helper}: {'yes' if hasattr(wren_core, helper) else 'no'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
