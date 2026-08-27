#!/usr/bin/env python3
"""List installed DeepPavlov config categories and config names.

This helper only inspects the installed package tree. It does not download
models, datasets, or weights.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


try:
    configs_module = importlib.import_module("deeppavlov.configs")
except Exception as exc:  # pragma: no cover - import failure is environment-specific
    print(f"Failed to import DeepPavlov configs: {exc}", file=sys.stderr)
    raise SystemExit(1)


CONFIG_ROOT = Path(configs_module.__file__).resolve().parent
CONFIG_TREE = configs_module.configs


def walk_tree(node: Dict[str, object], prefix: Tuple[str, ...] = ()) -> Iterable[Tuple[Tuple[str, ...], Path]]:
    """Yield (config_path_parts, file_path) pairs from the nested config tree."""
    for key in sorted(node.keys()):
        value = node[key]
        next_prefix = prefix + (key,)
        if isinstance(value, dict):
            yield from walk_tree(value, next_prefix)
        else:
            yield next_prefix, Path(value)


def collect_inventory() -> Dict[str, List[Dict[str, str]]]:
    inventory: Dict[str, List[Dict[str, str]]] = {}
    for parts, path in walk_tree(CONFIG_TREE._asdict()):
        category = parts[0]
        relative = path.resolve().relative_to(CONFIG_ROOT).as_posix()
        inventory.setdefault(category, []).append(
            {
                "name": "/".join(parts),
                "path": relative,
            }
        )
    for category in inventory:
        inventory[category].sort(key=lambda item: item["name"])
    return dict(sorted(inventory.items()))


def main() -> int:
    parser = argparse.ArgumentParser(description="List installed DeepPavlov config categories.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a grouped text list.")
    parser.add_argument(
        "--category",
        action="append",
        default=[],
        help="Limit output to one or more top-level categories such as classifiers or ner.",
    )
    parser.add_argument(
        "--show-paths",
        action="store_true",
        help="Include package-relative JSON file paths in text output.",
    )
    args = parser.parse_args()

    inventory = collect_inventory()
    if args.category:
        selected = [c for c in args.category if c in inventory]
        inventory = {c: inventory[c] for c in selected}

    if args.json:
        print(json.dumps(inventory, indent=2, ensure_ascii=False))
        return 0

    for category, items in inventory.items():
        print(category)
        for item in items:
            if args.show_paths:
                print(f"  - {item['name']}  [{item['path']}]")
            else:
                print(f"  - {item['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
