#!/usr/bin/env python3
"""Inspect torchtune's built-in recipe/config registry without importing recipes."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict


def load_registry():
    try:
        from torchtune._recipe_registry import get_all_recipes
    except Exception as exc:  # pragma: no cover - environment dependent
        raise SystemExit(f"Could not import torchtune._recipe_registry: {type(exc).__name__}: {exc}") from exc
    return get_all_recipes()


def recipe_to_dict(recipe):
    return {
        "name": recipe.name,
        "file_path": recipe.file_path,
        "supports_distributed": recipe.supports_distributed,
        "configs": [asdict(config) for config in recipe.configs],
    }


def print_table(recipes):
    rows = []
    for recipe in recipes:
        configs = recipe.configs or []
        if not configs:
            rows.append((recipe.name, "", "yes" if recipe.supports_distributed else "no"))
        for index, config in enumerate(configs):
            rows.append((recipe.name if index == 0 else "", config.name, "yes" if recipe.supports_distributed else "no" if index == 0 else ""))
    widths = [max([len(row[i]) for row in rows] + [len(header)]) for i, header in enumerate(("RECIPE", "CONFIG", "DISTRIBUTED"))]
    print(f"{'RECIPE':<{widths[0]}}  {'CONFIG':<{widths[1]}}  {'DISTRIBUTED':<{widths[2]}}")
    print(f"{'-' * widths[0]}  {'-' * widths[1]}  {'-' * widths[2]}")
    for recipe, config, distributed in rows:
        print(f"{recipe:<{widths[0]}}  {config:<{widths[1]}}  {distributed:<{widths[2]}}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print torchtune built-in recipe/config registry metadata without importing recipe modules.")
    parser.add_argument("--recipe", help="Filter to one recipe name.")
    parser.add_argument("--config", help="Filter to recipes containing one config name.")
    parser.add_argument("--format", choices=("table", "json"), default="table", help="Output format.")
    args = parser.parse_args(argv)

    recipes = load_registry()
    if args.recipe:
        recipes = [recipe for recipe in recipes if recipe.name == args.recipe]
    if args.config:
        recipes = [recipe for recipe in recipes if any(config.name == args.config for config in recipe.configs)]

    if not recipes:
        target = args.recipe or args.config or "<all>"
        print(f"No registry entries matched {target!r}.", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps([recipe_to_dict(recipe) for recipe in recipes], indent=2, sort_keys=True))
    else:
        print_table(recipes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
