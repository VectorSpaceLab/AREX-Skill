#!/usr/bin/env python3
"""Read-only queries over an explicit ClawBio skills/catalog.json file.

This helper treats catalog content as data. It does not import ClawBio, execute
``demo_command`` values, invoke a shell, inspect skill code, or make network
requests.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Query ClawBio catalog metadata without executing skills."
    )
    parser.add_argument(
        "--catalog",
        required=True,
        type=Path,
        metavar="PATH",
        help="Explicit path to skills/catalog.json (required).",
    )
    parser.add_argument("--name", help="Match a skill directory name exactly.")
    parser.add_argument("--alias", help="Match a CLI alias exactly.")
    parser.add_argument(
        "--keyword",
        help="Case-insensitive substring match across name, description, tags, and trigger keywords.",
    )
    parser.add_argument(
        "--maturity-tier",
        help="Match the catalog maturity_tier exactly, such as cli-registered or tested.",
    )
    registered = parser.add_mutually_exclusive_group()
    registered.add_argument(
        "--registered",
        action="store_true",
        help="Show entries whose maturity evidence says cli_registered=true.",
    )
    registered.add_argument(
        "--agent-readable-only",
        action="store_true",
        help="Show entries whose maturity evidence says cli_registered=false.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print catalog counts instead of individual matching entries.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        metavar="N",
        help="Maximum entries to print (default: 50; must be positive).",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        dest="output_format",
        help="Output format for entries or summary (default: table).",
    )
    return parser


def _load_catalog(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read catalog {path}: {exc}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"catalog is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("skills"), list):
        raise ValueError("catalog must be an object containing a skills list")
    entries: list[dict[str, Any]] = []
    for index, entry in enumerate(payload["skills"]):
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            raise ValueError(f"catalog skills[{index}] must be an object with a string name")
        entries.append(entry)
    return payload, entries


def _registered(entry: dict[str, Any]) -> bool:
    evidence = entry.get("maturity_evidence")
    return isinstance(evidence, dict) and evidence.get("cli_registered") is True


def _text_blob(entry: dict[str, Any]) -> str:
    values: list[str] = [str(entry.get("name", "")), str(entry.get("description", ""))]
    for field in ("tags", "trigger_keywords", "chaining_partners"):
        value = entry.get(field, [])
        if isinstance(value, list):
            values.extend(str(item) for item in value)
    return " ".join(values).casefold()


def _matches(entry: dict[str, Any], args: argparse.Namespace) -> bool:
    if args.name is not None and entry.get("name") != args.name:
        return False
    if args.alias is not None and entry.get("cli_alias") != args.alias:
        return False
    if args.keyword is not None and args.keyword.casefold() not in _text_blob(entry):
        return False
    if args.maturity_tier is not None and entry.get("maturity_tier") != args.maturity_tier:
        return False
    if args.registered and not _registered(entry):
        return False
    if args.agent_readable_only and _registered(entry):
        return False
    return True


def _entry_view(entry: dict[str, Any]) -> dict[str, Any]:
    evidence = entry.get("maturity_evidence")
    if not isinstance(evidence, dict):
        evidence = {}
    return {
        "name": entry.get("name"),
        "cli_alias": entry.get("cli_alias"),
        "description": entry.get("description", ""),
        "status": entry.get("status"),
        "maturity_tier": entry.get("maturity_tier"),
        "cli_registered": evidence.get("cli_registered", False),
        "has_script": entry.get("has_script", False),
        "has_tests": entry.get("has_tests", False),
        "has_demo": entry.get("has_demo", False),
        "tags": entry.get("tags", []),
        "trigger_keywords": entry.get("trigger_keywords", []),
        "chaining_partners": entry.get("chaining_partners", []),
    }


def _summary(payload: dict[str, Any], entries: list[dict[str, Any]]) -> dict[str, Any]:
    tiers = Counter(str(entry.get("maturity_tier", "unknown")) for entry in entries)
    statuses = Counter(str(entry.get("status", "unknown")) for entry in entries)
    return {
        "catalog_version": payload.get("version"),
        "generated_by": payload.get("generated_by"),
        "declared_skill_count": payload.get("skill_count"),
        "entry_count": len(entries),
        "registered_count": sum(_registered(entry) for entry in entries),
        "agent_readable_only_count": sum(not _registered(entry) for entry in entries),
        "maturity_tiers": dict(sorted(tiers.items())),
        "statuses": dict(sorted(statuses.items())),
    }


def _print_table(entries: list[dict[str, Any]]) -> None:
    views = [_entry_view(entry) for entry in entries]
    headers = ("NAME", "ALIAS", "TIER", "STATUS", "REGISTERED", "SCRIPT", "TESTS", "DEMO")
    rows = [
        (
            str(view["name"]),
            str(view["cli_alias"] or "-"),
            str(view["maturity_tier"] or "-"),
            str(view["status"] or "-"),
            "yes" if view["cli_registered"] else "no",
            "yes" if view["has_script"] else "no",
            "yes" if view["has_tests"] else "no",
            "yes" if view["has_demo"] else "no",
        )
        for view in views
    ]
    widths = [max(len(headers[i]), *(len(row[i]) for row in rows)) for i in range(len(headers))]
    print("  ".join(headers[i].ljust(widths[i]) for i in range(len(headers))))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(row[i].ljust(widths[i]) for i in range(len(headers))))


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.limit <= 0:
        print("error: --limit must be positive", file=sys.stderr)
        return 2
    try:
        payload, entries = _load_catalog(args.catalog)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    matching = [entry for entry in entries if _matches(entry, args)]
    if args.summary:
        result = _summary(payload, matching)
        if args.output_format == "json":
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(f"catalog_version: {result['catalog_version']}")
            print(f"entry_count: {result['entry_count']}")
            print(f"registered_count: {result['registered_count']}")
            print(f"agent_readable_only_count: {result['agent_readable_only_count']}")
            print("maturity_tiers:")
            for tier, count in result["maturity_tiers"].items():
                print(f"  {tier}: {count}")
            print("statuses:")
            for status, count in result["statuses"].items():
                print(f"  {status}: {count}")
        return 0

    selected = matching[: args.limit]
    if args.output_format == "json":
        print(json.dumps([_entry_view(entry) for entry in selected], indent=2, sort_keys=True))
    else:
        _print_table(selected)
        if len(matching) > len(selected):
            print(f"... {len(matching) - len(selected)} additional match(es); increase --limit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
