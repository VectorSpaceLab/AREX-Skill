#!/usr/bin/env python3
"""List discovered analyses and indexers for prediction-market-analysis.

This helper is safe and read-only. It walks upward from its own location to
find the repo root, then prints the discovered analysis and indexer classes.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "pyproject.toml").exists() and (candidate / "main.py").exists() and (candidate / "src").exists():
            return candidate
    raise SystemExit("Could not find the repo root from the catalog helper location.")


def _print_catalog(kind: str, root: Path) -> None:
    # Add the repo root so the source package can be imported even when the
    # helper is launched from outside the checkout.
    sys.path.insert(0, str(root))

    try:
        if kind == "analyses":
            from src.common.analysis import Analysis

            items = Analysis.load(root / "src" / "analysis")
        else:
            from src.common.indexer import Indexer

            items = Indexer.load(root / "src" / "indexers")
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "The catalog helper needs the repo runtime dependencies. "
            "Run it with the prepared inspection environment or through `uv run`."
        ) from exc

    print(f"[{kind}] {len(items)} discovered")
    for cls in items:
        inst = cls()
        print(f"{inst.name}|{cls.__module__}|{inst.description}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, help="Override the repo root auto-detection")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--analyses", action="store_true", help="List only analyses")
    group.add_argument("--indexers", action="store_true", help="List only indexers")
    group.add_argument("--all", action="store_true", help="List both analyses and indexers")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_root = args.repo_root.resolve() if args.repo_root else _find_repo_root(script_dir)

    if args.indexers:
        _print_catalog("indexers", repo_root)
    elif args.analyses:
        _print_catalog("analyses", repo_root)
    else:
        _print_catalog("analyses", repo_root)
        _print_catalog("indexers", repo_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
