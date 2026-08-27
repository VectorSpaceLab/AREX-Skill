#!/usr/bin/env python3
"""Check a Python environment for tree-of-thoughts runtime readiness.

This helper performs import and metadata checks only. It does not call external
model APIs and does not require an OpenAI key.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib import metadata
from typing import Any


def _try_import(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - operator-facing path
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"name": name, "ok": True, "module": getattr(module, "__name__", name)}


def _dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def build_report() -> dict[str, Any]:
    imports = [
        _try_import("tree_of_thoughts"),
        _try_import("tree_of_thoughts.agent"),
        _try_import("tree_of_thoughts.dfs"),
        _try_import("tree_of_thoughts.bfs"),
    ]
    versions = {
        "tree-of-thoughts": _dist_version("tree-of-thoughts"),
        "swarms": _dist_version("swarms"),
        "swarm-models": _dist_version("swarm-models"),
        "langchain-community": _dist_version("langchain-community"),
        "pydantic": _dist_version("pydantic"),
    }

    public_api: dict[str, Any] = {"ok": False}
    try:
        from tree_of_thoughts import ToTDFSAgent, TotAgent
        from tree_of_thoughts.agent import Thought
        from tree_of_thoughts.bfs import BFSWithTotAgent

        fields = getattr(Thought, "model_fields", getattr(Thought, "__fields__", {}))
        public_api = {
            "ok": True,
            "root_exports": [TotAgent.__name__, ToTDFSAgent.__name__],
            "bfs_import": BFSWithTotAgent.__name__,
            "thought_fields": sorted(fields.keys()),
        }
    except Exception as exc:  # pragma: no cover - operator-facing path
        public_api = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    ok = all(item["ok"] for item in imports) and bool(versions["tree-of-thoughts"]) and public_api.get("ok")
    return {
        "ok": ok,
        "python": sys.version.split()[0],
        "versions": versions,
        "imports": imports,
        "public_api": public_api,
        "notes": [
            "BFSWithTotAgent is imported from tree_of_thoughts.bfs, not the root package.",
            "Real TotAgent model calls may require OPENAI_API_KEY; this check does not call any provider.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check tree-of-thoughts import and metadata readiness.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON only.")
    args = parser.parse_args()

    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
        if report["ok"]:
            print("READY: tree-of-thoughts import surface is available.")
        else:
            print("NOT READY: fix import/version errors above.", file=sys.stderr)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
