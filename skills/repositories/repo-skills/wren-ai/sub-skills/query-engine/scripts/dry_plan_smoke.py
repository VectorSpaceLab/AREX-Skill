#!/usr/bin/env python3
"""Run a Wren semantic dry plan without executing against a database.

Usage:
  python dry_plan_smoke.py --mdl target/mdl.json --datasource duckdb --sql 'SELECT * FROM orders'
"""
from __future__ import annotations

import argparse
import base64
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mdl", type=Path, required=True, help="compiled MDL JSON")
    parser.add_argument("--datasource", required=True, help="Wren datasource/dialect")
    parser.add_argument("--sql", required=True, help="SQL against MDL objects")
    args = parser.parse_args()
    if not args.mdl.is_file():
        parser.error(f"MDL file not found: {args.mdl}")
    try:
        from wren.engine import WrenEngine
    except ImportError as exc:
        print(f"Missing WrenAI base package: {exc}")
        return 2
    manifest = base64.b64encode(args.mdl.read_bytes()).decode("ascii")
    try:
        engine = WrenEngine(manifest, args.datasource, {})
        print(engine.dry_plan(args.sql))
    except Exception as exc:
        print(f"Dry-plan failed: {type(exc).__name__}: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
