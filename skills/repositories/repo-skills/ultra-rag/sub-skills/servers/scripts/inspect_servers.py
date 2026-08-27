#!/usr/bin/env python3
"""Inspect UltraRAG server modules from a checkout-aware environment.

This helper imports selected server modules, prints their public callables, and
reports missing optional dependencies clearly instead of surfacing a raw
traceback.

Usage:
  python inspect_servers.py --repo-root /path/to/UltraRAG
  python inspect_servers.py --repo-root /path/to/UltraRAG --module servers.generation.src.generation
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import sys
from pathlib import Path
from typing import Iterable

DEFAULT_MODULES = [
    "servers.benchmark.src.benchmark",
    "servers.corpus.src.corpus",
    "servers.evaluation.src.evaluation",
    "servers.generation.src.generation",
    "servers.memory.src.memory",
    "servers.prompt.src.prompt",
    "servers.reranker.src.reranker",
    "servers.retriever.src.retriever",
    "servers.custom.src.custom",
    "servers.sayhello.src.sayhello",
]


def _add_repo_paths(repo_root: Path) -> None:
    repo_root = repo_root.resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    retriever_src = repo_root / "servers" / "retriever" / "src"
    if retriever_src.exists() and str(retriever_src) not in sys.path:
        sys.path.insert(0, str(retriever_src))


def _iter_public_callables(module: object) -> Iterable[tuple[str, object]]:
    mod_name = getattr(module, "__name__", "")
    for name in sorted(dir(module)):
        if name.startswith("_"):
            continue
        try:
            obj = getattr(module, name)
        except AttributeError:
            continue
        if callable(obj) and getattr(obj, "__module__", None) == mod_name:
            yield name, obj


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Path to the UltraRAG checkout.",
    )
    parser.add_argument(
        "--module",
        action="append",
        help="Module to inspect. May be repeated. Defaults to all major server modules.",
    )
    parser.add_argument(
        "--max-symbols",
        type=int,
        default=40,
        help="Maximum public callables to print per module.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    _add_repo_paths(repo_root)

    modules = args.module or DEFAULT_MODULES
    exit_code = 0

    for mod_name in modules:
        try:
            module = importlib.import_module(mod_name)
        except Exception as exc:
            exit_code = 1
            print(f"{mod_name}: FAIL {type(exc).__name__}: {exc}")
            continue

        print(f"{mod_name}: OK")
        count = 0
        for name, obj in _iter_public_callables(module):
            try:
                sig = inspect.signature(obj)
            except Exception:
                sig = "(?)"
            print(f"  {name}{sig}")
            count += 1
            if count >= args.max_symbols:
                print("  ...")
                break

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
