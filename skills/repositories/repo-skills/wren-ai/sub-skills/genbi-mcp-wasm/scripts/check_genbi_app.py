#!/usr/bin/env python3
"""Perform a static, no-deploy preflight for a GenBI app directory.

Usage:
  python check_genbi_app.py --app apps/sales --data-mode snapshot
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SECRET = re.compile(r"(?i)(password|api[_-]?key|access[_-]?token|secret)\s*[:=]\s*['\"][^'\"]{8,}['\"]")
BINARY_SUFFIXES = {".parquet", ".duckdb", ".wasm", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".zip"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, required=True)
    parser.add_argument("--data-mode", choices=("snapshot", "live"), default="snapshot")
    args = parser.parse_args()
    app = args.app.expanduser().resolve()
    failures: list[str] = []
    if not app.is_dir():
        failures.append("app directory missing")
    else:
        if not (app / "index.html").is_file():
            failures.append("missing index.html")
        mdl = app / "mdl.json"
        if not mdl.is_file():
            failures.append("missing mdl.json")
        else:
            try:
                if not json.loads(mdl.read_text(encoding="utf-8")):
                    failures.append("mdl.json is empty")
            except (OSError, json.JSONDecodeError) as exc:
                failures.append(f"invalid mdl.json: {exc}")
        if args.data_mode == "snapshot":
            assets = [p for p in app.rglob("*") if p.is_file() and p.suffix.lower() in {".parquet", ".duckdb"}]
            if not assets:
                failures.append("snapshot mode needs a .parquet or .duckdb asset")
        for path in app.rglob("*"):
            if not path.is_file() or path.is_symlink():
                continue
            if path.name.startswith(".env"):
                failures.append(f"must not ship environment file: {path.relative_to(app)}")
            elif path.suffix.lower() not in BINARY_SUFFIXES:
                try:
                    if SECRET.search(path.read_text(errors="ignore")):
                        failures.append(f"possible inline secret: {path.relative_to(app)}")
                except OSError:
                    pass
    if failures:
        print("GenBI static preflight failed:")
        print("\n".join(f"- {item}" for item in failures))
        return 1
    print("GenBI static preflight passed. No browser, provider, or network call was made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
