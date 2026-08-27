#!/usr/bin/env python3
"""Inspect Autodistill's model registry without installing plugins.

The script imports `autodistill.registry`, prints aliases/classes/default
constructor arguments, and optionally reports whether each plugin module is
currently importable. It does not call import_requisite_module() and never runs
pip install.
"""
from __future__ import annotations

import argparse
import importlib.util
from typing import Iterable

from autodistill import registry


def module_import_name(alias: str) -> str:
    return "autodistill_" + alias


def rows() -> Iterable[tuple[str, str, str, str]]:
    for entry in registry.AUTODISTILL_MODULES:
        alias = entry[0]
        class_name = entry[1]
        default_arg = entry[2] if len(entry) > 2 else ""
        yield alias, module_import_name(alias), class_name, default_arg


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-installed",
        action="store_true",
        help="Also check whether each registry import module is importable without importing it.",
    )
    parser.add_argument(
        "--alias",
        default=None,
        help="Show only one alias.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selected = list(rows())
    if args.alias:
        selected = [row for row in selected if row[0] == args.alias]
        if not selected:
            raise SystemExit(f"Alias {args.alias!r} is not in the Autodistill registry")
    header = ["alias", "import_module", "class", "default_arg"]
    if args.check_installed:
        header.append("importable")
    print("\t".join(header))
    for alias, import_name, class_name, default_arg in selected:
        values = [alias, import_name, class_name, default_arg]
        if args.check_installed:
            values.append("yes" if importlib.util.find_spec(import_name) else "no")
        print("\t".join(values))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
