#!/usr/bin/env python3
"""Check Wren query dependencies and optionally list a datasource's required extra.

Usage:
  python check_wren_environment.py
  python check_wren_environment.py --datasource postgres
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata


EXTRAS = {
    "postgres": "postgres", "mysql": "mysql", "bigquery": "bigquery",
    "snowflake": "snowflake", "clickhouse": "clickhouse", "trino": "trino",
    "mssql": "mssql", "databricks": "databricks", "redshift": "redshift",
    "spark": "spark", "athena": "athena", "oracle": "oracle",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasource", choices=sorted(EXTRAS))
    args = parser.parse_args()
    errors = []
    for module in ("wren", "wren_core"):
        try:
            importlib.import_module(module)
            print(f"import {module}: OK")
        except Exception as exc:
            errors.append(f"{module}: {type(exc).__name__}: {exc}")
    for dist in ("wrenai", "wren-core-py"):
        try:
            print(f"{dist}: {importlib.metadata.version(dist)}")
        except importlib.metadata.PackageNotFoundError:
            errors.append(f"missing distribution {dist}")
    if args.datasource:
        print(f"Install guidance: pip install 'wrenai[{EXTRAS[args.datasource]}]'")
        print("This helper does not test credentials or a live database.")
    if errors:
        print("Failures:")
        print("\n".join(f"- {e}" for e in errors))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
