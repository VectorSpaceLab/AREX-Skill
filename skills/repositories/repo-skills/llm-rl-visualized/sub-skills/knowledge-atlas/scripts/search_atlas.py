#!/usr/bin/env python3
"""Safe, self-contained search helper for the knowledge atlas."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from textwrap import shorten

INDEX_PATH = Path(__file__).resolve().parents[1] / "references" / "atlas-index.json"


def load_index() -> dict:
    if not INDEX_PATH.exists():
        raise FileNotFoundError(f"atlas index not found: {INDEX_PATH}")
    with INDEX_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    entries = data.get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("atlas index is missing a valid 'entries' list")
    return data


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w一-鿿]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+|[一-鿿]+", normalize(text))


def flatten(entry: dict) -> dict[str, str]:
    return {
        "id": entry.get("id", ""),
        "category": entry.get("category", ""),
        "concept": entry.get("concept", ""),
        "aliases": " ".join(entry.get("aliases", [])),
        "diagram_families": " ".join(entry.get("diagram_families", [])),
        "notes": entry.get("notes", ""),
        "targets": " ".join(entry.get("targets", [])),
        "provenance": " ".join(entry.get("provenance", [])),
        "languages": " ".join(entry.get("languages", [])),
    }


def category_match(entry: dict, category: str) -> bool:
    if not category:
        return True
    needle = normalize(category)
    haystacks = [
        entry.get("category", ""),
        entry.get("id", ""),
        entry.get("concept", ""),
        " ".join(entry.get("aliases", [])),
        " ".join(entry.get("diagram_families", [])),
    ]
    return any(needle in normalize(hay) for hay in haystacks if hay)


def score_entry(entry: dict, query: str) -> tuple[int, list[str]]:
    q = normalize(query)
    if not q:
        return 1, []

    fields = flatten(entry)
    weights = {
        "id": 150,
        "concept": 140,
        "category": 130,
        "aliases": 125,
        "diagram_families": 100,
        "notes": 60,
        "targets": 40,
        "provenance": 30,
        "languages": 5,
    }

    reasons: list[str] = []
    score = 0
    for name, value in fields.items():
        norm_value = normalize(value)
        if not norm_value:
            continue
        if q == norm_value:
            score += weights[name] + 20
            reasons.append(name)
        elif q in norm_value:
            score += weights[name]
            reasons.append(name)

    tokens = tokenize(query)
    if tokens:
        all_text = " ".join(fields.values())
        norm_all = normalize(all_text)
        if all(token in norm_all for token in tokens):
            score += 35
            reasons.append("tokens")

    if not reasons:
        return 0, []

    deduped: list[str] = []
    for reason in reasons:
        if reason not in deduped:
            deduped.append(reason)
    return score, deduped


def fmt_list(items: list[str], width: int = 120) -> str:
    text = ", ".join(items)
    return shorten(text, width=width, placeholder=" …") if text else "-"


def list_categories(data: dict) -> int:
    entries = data.get("entries", [])
    counts = Counter(entry.get("category", "") for entry in entries if entry.get("category"))
    print("Categories:")
    for category, count in sorted(counts.items(), key=lambda item: (item[0].lower(), item[0])):
        print(f"- {category} ({count})")
    return 0


def render_entry(entry: dict, rank: int, score: int, reasons: list[str]) -> None:
    print(f"{rank}. {entry.get('id', '-')} — {entry.get('category', '-')} (score {score})")
    print(f"   concept: {shorten(entry.get('concept', '-'), width=120, placeholder=' …')}")
    print(f"   aliases: {fmt_list(entry.get('aliases', []))}")
    print(f"   languages: {fmt_list(entry.get('languages', []), width=20)}")
    print(f"   diagram families: {fmt_list(entry.get('diagram_families', []), width=150)}")
    print(f"   targets: {fmt_list(entry.get('targets', []), width=120)}")
    print(f"   provenance: {fmt_list(entry.get('provenance', []), width=140)}")
    note = entry.get('notes', '')
    if note:
        print(f"   note: {shorten(note, width=120, placeholder=' …')}")
    if reasons:
        print(f"   matched on: {', '.join(reasons)}")


def search_entries(data: dict, query: str | None, category: str | None, limit: int) -> list[tuple[int, dict, list[str]]]:
    entries = data.get("entries", [])
    results: list[tuple[int, dict, list[str]]] = []
    for entry in entries:
        if not category_match(entry, category or ""):
            continue
        score, reasons = score_entry(entry, query or "")
        if query and score <= 0:
            continue
        if not query:
            score = 1
            reasons = ["category"] if category else []
        results.append((score, entry, reasons))
    results.sort(key=lambda item: (-item[0], item[1].get("category", ""), item[1].get("concept", ""), item[1].get("id", "")))
    return results[:limit]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search the distilled knowledge atlas.")
    parser.add_argument("--query", help="Text query such as PPO, GRPO, RoPE, RAG, or model catalog.")
    parser.add_argument("--category", help="Filter by category, id, concept, alias, or diagram family.")
    parser.add_argument("--list-categories", action="store_true", help="List atlas categories and exit.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of matches to display.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        data = load_index()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.list_categories:
        return list_categories(data)

    if not args.query and not args.category:
        parser.print_help()
        return 0

    matches = search_entries(data, args.query, args.category, max(1, args.limit))
    if not matches:
        print("No atlas matches found.")
        if args.query:
            print(f"Try the acronym, the full English term, or the Chinese alias for: {args.query}")
        print("Use --list-categories to browse families.")
        return 1

    title = args.query or args.category or "atlas"
    print(f"Matches for {title!r} ({len(matches)}):")
    for idx, (score, entry, reasons) in enumerate(matches, start=1):
        render_entry(entry, idx, score, reasons)
        if idx != len(matches):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
