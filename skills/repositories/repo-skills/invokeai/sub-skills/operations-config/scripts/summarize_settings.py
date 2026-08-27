#!/usr/bin/env python3
"""Summarize the bundled InvokeAI generated settings catalog."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "references" / "settings-catalog.json"


def load_catalog(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Settings catalog not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Settings catalog is not valid JSON: {path}: {exc}")
    settings = payload.get("settings") if isinstance(payload, dict) else None
    if not isinstance(settings, list):
        raise SystemExit(f"Settings catalog has unexpected shape: {path}")
    return [item for item in settings if isinstance(item, dict)]


def normalize(text: str) -> str:
    return text.casefold().replace(" ", "_").replace("-", "_")


def filter_settings(settings: list[dict[str, Any]], category: str | None, search: str | None) -> list[dict[str, Any]]:
    filtered = settings
    if category:
        wanted = normalize(category)
        filtered = [item for item in filtered if normalize(str(item.get("category", ""))) == wanted]
    if search:
        needle = search.casefold()
        filtered = [
            item
            for item in filtered
            if needle in str(item.get("name", "")).casefold()
            or needle in str(item.get("description", "")).casefold()
            or needle in str(item.get("env_var", "")).casefold()
        ]
    return filtered


def print_categories(settings: list[dict[str, Any]]) -> None:
    grouped: dict[str, int] = defaultdict(int)
    for item in settings:
        grouped[str(item.get("category", "UNCATEGORIZED"))] += 1
    for category, count in sorted(grouped.items(), key=lambda pair: pair[0].casefold()):
        print(f"{category}: {count}")


def format_default(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def print_settings(settings: list[dict[str, Any]], verbose: bool) -> None:
    if not settings:
        print("No settings matched.")
        return
    for item in settings:
        name = item.get("name", "<unknown>")
        category = item.get("category", "UNCATEGORIZED")
        env_var = item.get("env_var") or "-"
        default = format_default(item.get("default"))
        literal_values = item.get("literal_values") or []
        print(f"{category} / {name}")
        print(f"  env: {env_var}")
        print(f"  default: {default}")
        if literal_values:
            print(f"  values: {', '.join(map(str, literal_values))}")
        if verbose:
            print(f"  type: {item.get('type', '-')}")
            print(f"  required: {item.get('required', False)}")
            validation = item.get("validation") or {}
            if validation:
                print(f"  validation: {json.dumps(validation, sort_keys=True)}")
            description = str(item.get("description", "")).replace("\n", " ").strip()
            print(f"  description: {description or '-'}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize bundled InvokeAI settings metadata.")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG, help="Path to settings-catalog.json.")
    parser.add_argument("--categories", action="store_true", help="List categories and counts only.")
    parser.add_argument("--category", help="Show settings in a category such as WEB, PATHS, LOGGING, or MULTIUSER.")
    parser.add_argument("--search", help="Filter settings by name, env var, or description text.")
    parser.add_argument("--json", action="store_true", help="Emit matched settings as JSON.")
    parser.add_argument("--verbose", action="store_true", help="Include type, validation, and descriptions.")
    args = parser.parse_args()

    settings = load_catalog(args.catalog)
    if args.categories:
        print_categories(settings)
        return 0

    filtered = filter_settings(settings, args.category, args.search)
    if args.json:
        json.dump({"settings": filtered}, sys.stdout, indent=2, sort_keys=True)
        print()
    else:
        print_settings(filtered, args.verbose)
    return 0


if __name__ == "__main__":
    sys.exit(main())
