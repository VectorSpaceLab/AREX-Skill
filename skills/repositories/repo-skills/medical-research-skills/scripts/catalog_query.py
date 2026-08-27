#!/usr/bin/env python3
"""Search the bundled medical-research-skills discovery index.

This helper is deterministic and offline. It never imports a catalog skill,
opens a checkout, downloads data, or executes a result. Use it to identify a
specialist skill id and then read the corresponding installed/catalog entry if
that entry is available in the caller's environment.

Example:
    python scripts/catalog_query.py "bulk RNA-seq differential expression" --limit 5
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


DEFAULT_INDEX = Path(__file__).resolve().parents[1] / "references" / "catalog-index.json"


def load_index(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError as exc:
        raise SystemExit(f"catalog index not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"catalog index is invalid JSON: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("collections"), dict):
        raise SystemExit("catalog index has an unsupported schema")
    return payload


def entries(index: dict[str, Any]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for collection, collection_data in index["collections"].items():
        categories = collection_data.get("categories", {})
        if not isinstance(categories, dict):
            continue
        for category, category_data in categories.items():
            for item in category_data.get("skills", []):
                if isinstance(item, dict):
                    record = dict(item)
                    record.setdefault("collection", collection)
                    record.setdefault("category", category)
                    found.append(record)
    return found


def score(record: dict[str, Any], query_tokens: list[str]) -> tuple[int, str]:
    skill_id = str(record.get("id", ""))
    name = str(record.get("name", ""))
    description = str(record.get("description", ""))
    category = str(record.get("category", ""))
    signals = " ".join(str(x) for x in record.get("signals", []))
    haystack = " ".join((skill_id, name, description, category, signals)).casefold()
    value = 0
    for token in query_tokens:
        if token in skill_id.casefold():
            value += 12
        elif token in name.casefold():
            value += 9
        elif token in category.casefold():
            value += 5
        elif token in description.casefold():
            value += 3
        elif token in signals.casefold():
            value += 2
    phrase = " ".join(query_tokens)
    if phrase and phrase in haystack:
        value += 8
    if skill_id.casefold() == phrase:
        value += 100
    return value, skill_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Search the bundled offline catalog index.")
    parser.add_argument("query", nargs="?", help="Task phrase, package/specialty name, or skill id.")
    parser.add_argument("--collection", choices=("scientific-skills", "awesome-med-research-skills"))
    parser.add_argument("--category", help="Exact category, for example 'Data Analysis'.")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit matching records as JSON.")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.limit < 1 or args.limit > 100:
        parser.error("--limit must be between 1 and 100")
    if not args.query and not args.category and not args.collection:
        parser.error("provide a query, --category, or --collection")

    index = load_index(args.index)
    records = entries(index)
    if args.collection:
        records = [r for r in records if r.get("collection") == args.collection]
    if args.category:
        wanted = args.category.casefold()
        records = [r for r in records if str(r.get("category", "")).casefold() == wanted]

    if args.query:
        tokens = [t for t in re.findall(r"[a-z0-9][a-z0-9+.-]*", args.query.casefold()) if len(t) > 1]
        ranked = [(score(record, tokens)[0], record) for record in records]
        ranked = [(points, record) for points, record in ranked if points > 0]
        ranked.sort(key=lambda pair: (-pair[0], str(pair[1].get("id", ""))))
        matches = [record for _, record in ranked[: args.limit]]
    else:
        matches = sorted(records, key=lambda record: (str(record.get("category", "")), str(record.get("id", ""))))[: args.limit]

    if args.as_json:
        print(json.dumps(matches, ensure_ascii=False, indent=2))
    else:
        for record in matches:
            print(f"{record.get('id')}\t[{record.get('collection')}/{record.get('category')}]\t{record.get('description', '')}")
    if not matches:
        print("No catalog matches. Broaden the task phrase or inspect the category route.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
