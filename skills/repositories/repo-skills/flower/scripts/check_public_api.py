#!/usr/bin/env python3
"""Recursively verify that public `__all__` exports are importable.

Use this to confirm that the public API surface of a package is internally
consistent after refactors or release checks.

Examples
--------
python scripts/check_public_api.py flwr flwr_datasets
python scripts/check_public_api.py --max-depth 4 flwr
"""

from __future__ import annotations

import argparse
import importlib
from types import ModuleType
from typing import Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "packages",
        nargs="+",
        help="One or more top-level packages to inspect.",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=8,
        help="Maximum recursive depth for nested modules that expose __all__.",
    )
    return parser.parse_args()


def is_module(value: object) -> bool:
    return isinstance(value, ModuleType)


def check_package(name: str, max_depth: int, depth: int = 0, seen: set[str] | None = None) -> list[str]:
    if seen is None:
        seen = set()
    if name in seen:
        return []
    seen.add(name)

    problems: list[str] = []
    module = importlib.import_module(name)
    exports: Iterable[str] = getattr(module, "__all__", [])
    if not exports:
        print(f"[ok] {name}: no __all__ found")
        return problems

    print(f"[ok] {name}: checking {len(list(exports))} exported names")
    # Re-evaluate exports after the length check because iterables may be
    # consumed when they are not real lists.
    exports = getattr(module, "__all__", [])
    for exported_name in exports:
        if not hasattr(module, exported_name):
            problems.append(f"{name}: missing export {exported_name!r}")
            continue
        exported = getattr(module, exported_name)
        if is_module(exported) and depth < max_depth and hasattr(exported, "__all__"):
            problems.extend(check_package(exported.__name__, max_depth, depth + 1, seen))
        elif is_module(exported) and depth < max_depth and getattr(exported, "__path__", None):
            # Imported submodule/package without __all__; importability is enough.
            print(f"[ok] {exported.__name__}: importable module export")
        else:
            print(f"[ok] {name}.{exported_name}: importable")
    return problems


def main() -> None:
    args = parse_args()
    problems: list[str] = []
    for package in args.packages:
        try:
            problems.extend(check_package(package, args.max_depth))
        except Exception as exc:
            problems.append(f"{package}: {exc}")

    if problems:
        print("\nProblems:")
        for problem in problems:
            print(f"- {problem}")
        raise SystemExit(1)

    print("All requested public exports were importable.")


if __name__ == "__main__":
    main()
