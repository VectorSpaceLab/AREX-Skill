#!/usr/bin/env python3
"""Safe high-level Nexent checkout probe.

This helper reports package metadata files, important source directories, and
whether bundled static sub-skill helpers can see their expected checkout files.
It does not import Nexent, start services, connect to infrastructure, or run
native tests.

Examples:
  python nexent_static_probe.py --repo-root /path/to/nexent
  python nexent_static_probe.py --repo-root /path/to/nexent --json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

IMPORTANT_PATHS = [
    "sdk/pyproject.toml",
    "sdk/nexent",
    "backend/pyproject.toml",
    "backend/apps",
    "backend/services",
    "backend/consts/const.py",
    "frontend/package.json",
    "frontend/services",
    "frontend/types",
    "deploy/env/.env.example",
    "deploy/sql/init.sql",
    "deploy/sql/migrations",
    "VERSION",
    "AGENTS.md",
]


def describe(path: Path, rel: str) -> dict[str, Any]:
    target = path / rel
    kind = "missing"
    if target.is_dir():
        kind = "dir"
    elif target.is_file():
        kind = "file"
    return {"path": rel, "kind": kind, "exists": target.exists()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe Nexent checkout structure probe")
    parser.add_argument("--repo-root", required=True, help="Path to a Nexent checkout")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    result = {
        "repoRoot": str(repo_root),
        "paths": [describe(repo_root, rel) for rel in IMPORTANT_PATHS],
        "suggestedSubSkills": [
            "sdk-agent-runtime",
            "backend-services-api",
            "knowledge-data-memory",
            "frontend-integration",
            "deployment-operations",
        ],
    }
    missing = [item["path"] for item in result["paths"] if not item["exists"]]
    result["warnings"] = [f"Missing expected path: {item}" for item in missing]

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        for item in result["paths"]:
            marker = "OK" if item["exists"] else "MISSING"
            print(f"{marker:7} {item['kind']:7} {item['path']}")
        for warning in result["warnings"]:
            print(f"WARNING: {warning}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
