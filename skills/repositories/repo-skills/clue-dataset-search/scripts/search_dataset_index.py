#!/usr/bin/env python3
"""Search the bundled CLUEDatasetSearch dataset index.

The generated repo skill bundles a distilled JSON index under
`references/dataset-index.json`; it does not bundle any original datasets.

Examples:
  python scripts/search_dataset_index.py --query dureader --limit 5
  python scripts/search_dataset_index.py --category text-matching --query finance --json
  python scripts/search_dataset_index.py --language Chinese --query sentiment
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable


def default_index_path() -> Path:
    return Path(__file__).resolve().parents[1] / "references" / "dataset-index.json"


def load_entries(index_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    data = json.loads(index_path.read_text(encoding="utf-8"))
    entries: list[dict[str, Any]] = []
    for category in data.get("categories", []):
        for entry in category.get("datasets", []):
            merged = dict(entry)
            merged.setdefault("category_slug", category.get("slug"))
            merged.setdefault("category_name", category.get("name"))
            entries.append(merged)
    return data, entries


def text_blob(entry: dict[str, Any]) -> str:
    paper = entry.get("paper") or {}
    parts: Iterable[Any] = [
        entry.get("title"),
        entry.get("category_slug"),
        entry.get("category_name"),
        entry.get("task_type"),
        entry.get("keywords"),
        entry.get("description"),
        entry.get("provider"),
        entry.get("license"),
        entry.get("note"),
        entry.get("url"),
        paper.get("title"),
        paper.get("url"),
        " ".join(entry.get("language_signals") or []),
    ]
    return "\n".join(str(p) for p in parts if p).casefold()


def matches(entry: dict[str, Any], args: argparse.Namespace) -> bool:
    if args.category:
        wanted = args.category.casefold()
        cat_values = [entry.get("category_slug", ""), entry.get("category_name", ""), entry.get("task_type", "")]
        if not any(wanted in str(value).casefold() for value in cat_values):
            return False
    if args.language:
        wanted = args.language.casefold()
        langs = " ".join(entry.get("language_signals") or [])
        if wanted not in langs.casefold():
            return False
    if args.query:
        terms = [term.casefold() for term in args.query]
        blob = text_blob(entry)
        if not all(term in blob for term in terms):
            return False
    return True


def display_entry(entry: dict[str, Any]) -> str:
    paper = entry.get("paper") or {}
    bits = [
        f"[{entry.get('category_slug')}/{entry.get('row_id')}] {entry.get('title')}",
        f"category={entry.get('category_name')} task={entry.get('task_type') or 'unspecified'}",
        f"language={','.join(entry.get('language_signals') or ['unspecified'])}",
    ]
    if entry.get("updated"):
        bits.append(f"updated={entry['updated']}")
    if entry.get("license"):
        bits.append(f"license={entry['license']}")
    if entry.get("url"):
        bits.append(f"url={entry['url']}")
    if paper.get("url"):
        bits.append(f"paper={paper['url']}")
    if entry.get("description"):
        bits.append(f"description={entry['description'][:220]}")
    return "\n  ".join(bits)


def main() -> int:
    parser = argparse.ArgumentParser(description="Search the bundled CLUEDatasetSearch dataset-index.json.")
    parser.add_argument("--index", type=Path, default=default_index_path(), help="Path to dataset-index.json (default: bundled index next to this script).")
    parser.add_argument("--query", action="append", default=[], help="Case-insensitive term that must appear in the entry. Repeat for AND search.")
    parser.add_argument("--category", help="Filter by category slug/name/task text, e.g. text-matching, 阅读理解, NER.")
    parser.add_argument("--language", help="Filter by inferred language signal, e.g. Chinese, English, Multilingual.")
    parser.add_argument("--limit", type=int, default=20, help="Maximum entries to print; use 0 for all matches.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a readable text summary.")
    args = parser.parse_args()

    if not args.index.exists():
        parser.error(f"index file not found: {args.index}")

    data, entries = load_entries(args.index)
    hits = [entry for entry in entries if matches(entry, args)]
    limited = hits if args.limit == 0 else hits[: max(args.limit, 0)]

    if args.json:
        print(json.dumps({"total_matches": len(hits), "returned": len(limited), "entries": limited}, ensure_ascii=False, indent=2))
        return 0

    print(f"Index: {data.get('source_repository', 'unknown')} | categories={data.get('category_count')} | entries={data.get('dataset_count')}")
    print(f"Matches: {len(hits)} | Returned: {len(limited)}")
    for entry in limited:
        print("\n" + display_entry(entry))
    if hits and len(limited) < len(hits):
        print(f"\n... {len(hits) - len(limited)} more match(es); increase --limit or use --limit 0.")
    if not hits:
        print("No matches. Try broader English/Chinese terms, a category name, or inspect references/catalogue-overview.md for category slugs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
