#!/usr/bin/env python3
"""Inspect OmicVerse MCP registry manifests without starting a server."""

from __future__ import annotations

import argparse
import json
import warnings
from collections import Counter
from typing import Any


def build_manifest(phase: str | None) -> tuple[list[dict[str, Any]], list[str]]:
    captured: list[str] = []
    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        from omicverse.mcp import get_manifest

        manifest = get_manifest(phase=phase)
        for record in records:
            captured.append(f"{record.category.__name__}: {record.message}")
    return manifest, captured


def compact_entry(entry: dict[str, Any], show_schema: bool) -> dict[str, Any]:
    keys = [
        "tool_name",
        "full_name",
        "kind",
        "execution_class",
        "adapter_type",
        "category",
        "description",
        "risk_level",
        "rollout_phase",
        "status",
        "availability",
    ]
    compact = {key: entry.get(key) for key in keys if key in entry}
    if show_schema:
        compact["parameter_schema"] = entry.get("parameter_schema")
        compact["state_contract"] = entry.get("state_contract")
        compact["dependency_contract"] = entry.get("dependency_contract")
        compact["return_contract"] = entry.get("return_contract")
    return compact


def search_manifest(manifest: list[dict[str, Any]], query: str | None) -> list[dict[str, Any]]:
    if not query:
        return manifest
    needle = query.lower()
    matches = []
    for entry in manifest:
        haystack = " ".join(
            str(entry.get(key, ""))
            for key in ("tool_name", "full_name", "category", "description", "rollout_phase", "status")
        ).lower()
        aliases = " ".join(str(alias) for alias in entry.get("aliases", [])).lower()
        if needle in haystack or needle in aliases:
            matches.append(entry)
    return matches


def summarize(manifest: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "tool_count": len(manifest),
        "by_phase": dict(sorted(Counter(str(entry.get("rollout_phase")) for entry in manifest).items())),
        "by_execution_class": dict(sorted(Counter(str(entry.get("execution_class")) for entry in manifest).items())),
        "by_category": dict(sorted(Counter(str(entry.get("category")) for entry in manifest).items())),
        "by_risk_level": dict(sorted(Counter(str(entry.get("risk_level")) for entry in manifest).items())),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List or search OmicVerse MCP registry manifest entries safely.")
    parser.add_argument("--phase", default="P0+P0.5", help="Manifest rollout phase filter, for example P0, P0+P0.5, or P0+P0.5+P2.")
    parser.add_argument("--all-phases", action="store_true", help="Do not pass a phase filter to get_manifest.")
    parser.add_argument("--search", default=None, help="Case-insensitive search across tool names, categories, descriptions, and aliases.")
    parser.add_argument("--limit", type=int, default=25, help="Maximum number of matching tools to print; use 0 for all.")
    parser.add_argument("--show-schema", action="store_true", help="Include parameter/state/dependency/return contracts for listed tools.")
    parser.add_argument("--categories", action="store_true", help="Only print summary/category counts and omit tool entries.")
    parser.add_argument("--warnings", action="store_true", help="Include captured Python warnings in the JSON output.")
    parser.add_argument("--output", default=None, help="Optional JSON output file path. Defaults to stdout.")
    args = parser.parse_args(argv)

    phase = None if args.all_phases else args.phase
    exit_code = 0
    try:
        manifest, captured_warnings = build_manifest(phase=phase)
        matches = search_manifest(manifest, args.search)
        selected = matches if args.limit == 0 else matches[: max(args.limit, 0)]
        report: dict[str, Any] = {
            "schema_version": 1,
            "ok": True,
            "phase": phase,
            "query": args.search,
            "summary": summarize(manifest),
            "match_count": len(matches),
            "safe_defaults": {
                "starts_services": False,
                "opens_network_listener": False,
                "executes_tools": False,
            },
        }
        if not args.categories:
            report["tools"] = [compact_entry(entry, args.show_schema) for entry in selected]
        if args.warnings:
            report["warnings"] = captured_warnings
    except Exception as exc:
        exit_code = 1
        report = {
            "schema_version": 1,
            "ok": False,
            "phase": phase,
            "query": args.search,
            "error": f"{type(exc).__name__}: {exc}",
            "safe_defaults": {
                "starts_services": False,
                "opens_network_listener": False,
                "executes_tools": False,
            },
        }

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.write("\n")
    else:
        print(text)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
