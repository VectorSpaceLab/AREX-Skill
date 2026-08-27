#!/usr/bin/env python3
"""Read-only Kotaemon installation diagnostic.

This script checks metadata/import signals for a Kotaemon checkout or Python
environment. It never starts the Gradio app, calls provider APIs, downloads
assets, indexes documents, or mutates app data.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import os
import sys
from pathlib import Path
from typing import Any


DISTRIBUTIONS = ["kotaemon-app", "kotaemon", "ktem"]
IMPORTS = ["kotaemon", "ktem"]
OPTIONAL_IMPORTS = {
    "gradio": "app UI",
    "langchain": "LLM provider wrappers and chains",
    "llama_index": "document/index utilities",
    "chromadb": "default vector store option",
    "lancedb": "vector/document store option",
    "openai": "OpenAI-compatible providers",
    "cohere": "Cohere chat/reranking providers",
    "docling": "Docling parser integration",
    "paddleocr": "PaddleOCR parser integration",
    "unstructured": "unstructured document parser",
    "mcp": "MCP integration",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose a Kotaemon installation without side effects.")
    parser.add_argument("--repo-root", type=Path, help="Optional Kotaemon checkout root to add package paths for import checks.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    return parser.parse_args()


def add_repo_paths(repo_root: Path | None) -> list[str]:
    added: list[str] = []
    if not repo_root:
        return added
    root = repo_root.expanduser().resolve()
    for relative in ("libs/kotaemon", "libs/ktem"):
        candidate = root / relative
        if candidate.exists():
            sys.path.insert(0, str(candidate))
            added.append(relative)
    return added


def dist_info(name: str) -> dict[str, Any]:
    try:
        requires = metadata.requires(name) or []
        return {
            "name": name,
            "installed": True,
            "version": metadata.version(name),
            "requires_count": len(requires),
        }
    except metadata.PackageNotFoundError:
        return {"name": name, "installed": False}


def import_info(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
        return {"name": name, "ok": True, "file": bool(getattr(module, "__file__", None))}
    except Exception as exc:
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def console_scripts() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for entry in metadata.entry_points().select(group="console_scripts"):
        if entry.name == "kotaemon" or entry.value.startswith("kotaemon"):
            rows.append({"name": entry.name, "value": entry.value})
    return rows


def main() -> int:
    args = parse_args()
    added = add_repo_paths(args.repo_root)
    result = {
        "python": sys.version.split()[0],
        "repo_paths_added": added,
        "distributions": [dist_info(name) for name in DISTRIBUTIONS],
        "imports": [import_info(name) for name in IMPORTS],
        "optional_imports": {name: {"purpose": purpose, **import_info(name)} for name, purpose in OPTIONAL_IMPORTS.items()},
        "console_scripts": console_scripts(),
        "environment_signals": {
            "has_openai_key": bool(os.environ.get("OPENAI_API_KEY")),
            "has_azure_key": bool(os.environ.get("AZURE_OPENAI_API_KEY")),
            "has_graphrag_key": bool(os.environ.get("GRAPHRAG_API_KEY")),
            "use_nano_graphrag": os.environ.get("USE_NANO_GRAPHRAG"),
            "use_lightrag": os.environ.get("USE_LIGHTRAG"),
        },
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Python: {result['python']}")
        if added:
            print(f"Repo package paths added: {', '.join(added)}")
        print("\nDistributions:")
        for row in result["distributions"]:
            if row["installed"]:
                print(f"  OK {row['name']} {row['version']} ({row['requires_count']} requirements declared)")
            else:
                print(f"  MISSING {row['name']}")
        print("\nImports:")
        for row in result["imports"]:
            print(f"  {'OK' if row['ok'] else 'FAIL'} {row['name']}" + (f" - {row.get('error')}" if not row["ok"] else ""))
        print("\nOptional packages:")
        for name, row in result["optional_imports"].items():
            status = "OK" if row["ok"] else "missing"
            print(f"  {status:7} {name:16} {row['purpose']}")
        if result["console_scripts"]:
            print("\nConsole scripts:")
            for row in result["console_scripts"]:
                print(f"  {row['name']} -> {row['value']}")
        print("\nNo provider APIs, app servers, downloads, or migrations were executed.")

    hard_fail = any(not row["ok"] for row in result["imports"])
    return 1 if hard_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
