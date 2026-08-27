#!/usr/bin/env python3
"""Search the bundled Papers-in-100-Lines implementation catalog.

This helper is intentionally stdlib-only. It reads the generated skill's
references/implementation-index.json and does not import or execute any upstream
paper implementation.

Examples:
  python scripts/query_implementation_index.py --query "stable diffusion"
  python scripts/query_implementation_index.py --group neural-rendering-3d --limit 20
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from textwrap import shorten


def default_index_path() -> Path:
    return Path(__file__).resolve().parents[1] / "references" / "implementation-index.json"


def load_entries(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("entries", [])


def _strings(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if item is not None]
    return [str(value)]


def score(entry: dict, query: str) -> float:
    if not query:
        return 1.0
    fields: list[str] = []
    for name in (
        "paper_title",
        "title",
        "name",
        "source_directory_evidence_label",
        "directory",
        "dir",
        "owner_sub_skill",
        "owner",
        "group",
        "backend_posture",
        "full_run_safety",
    ):
        fields.extend(_strings(entry.get(name)))
    for name in ("aliases", "categories", "python_scripts", "scripts", "key_symbols", "symbols", "requirements"):
        fields.extend(_strings(entry.get(name)))
    haystack = " ".join(fields).replace("_", " ").replace("-", " ").lower()
    query_norm = query.lower().replace("_", " ").replace("-", " ").strip()
    terms = [term for term in query_norm.split() if term]
    total = sum(1.0 for term in terms if term in haystack)
    if query_norm and query_norm in haystack:
        total += 10.0
    # Strongly prefer explicit aliases and exact title/directory phrases.
    alias_text = " ".join(_strings(entry.get("aliases"))).replace("_", " ").replace("-", " ").lower()
    if query_norm and query_norm in alias_text:
        total += 25.0
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="Search the bundled Papers-in-100-Lines implementation catalog.")
    parser.add_argument("--index-json", type=Path, default=default_index_path(), help="Path to implementation-index.json")
    parser.add_argument("--query", default="", help="Text to search across paper titles, evidence labels, scripts, and symbols")
    parser.add_argument("--group", choices=["generative-models", "neural-rendering-3d", "optimization-meta-rl"], help="Restrict to one owner sub-skill")
    parser.add_argument("--limit", type=int, default=10, help="Maximum entries to print")
    parser.add_argument("--json", action="store_true", help="Emit matching entries as JSON")
    args = parser.parse_args()

    entries = load_entries(args.index_json)
    if args.group:
        entries = [e for e in entries if e.get("owner_sub_skill") == args.group]
    ranked = [(score(e, args.query), e) for e in entries]
    ranked = [(s, e) for s, e in ranked if s > 0]
    ranked.sort(key=lambda item: (-item[0], item[1].get("paper_title", "")))
    matches = [e for _, e in ranked[: max(args.limit, 0)]]

    if args.json:
        print(json.dumps(matches, indent=2))
        return 0

    if not matches:
        print("No catalog entries matched. Try fewer terms or omit --group.")
        return 1

    for e in matches:
        scripts = ", ".join(e.get("python_scripts", [])) or "no scripts recorded"
        symbols = ", ".join(e.get("key_symbols", [])[:8]) or "no symbols recorded"
        print(f"- {e.get('paper_title')}")
        print(f"  group: {e.get('owner_sub_skill')}")
        print(f"  evidence label: {e.get('source_directory_evidence_label')}")
        print(f"  scripts: {scripts}")
        print(f"  backend: {e.get('backend_posture')}")
        print(f"  safety: {shorten(e.get('full_run_safety', ''), width=110, placeholder=' ...')}")
        print(f"  symbols: {symbols}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
