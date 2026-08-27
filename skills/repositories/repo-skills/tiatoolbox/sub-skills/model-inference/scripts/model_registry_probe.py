#!/usr/bin/env python3
"""Safely summarize TIAToolbox pretrained_model.yaml without downloading weights."""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


_ENTRY_RE = re.compile(r"^([A-Za-z0-9_.+-]+):\s*$")


def default_registry_path() -> Path:
    """Return the installed-package pretrained_model.yaml path without importing TIAToolbox."""
    spec = importlib.util.find_spec("tiatoolbox")
    if spec and spec.submodule_search_locations:
        for package_dir in spec.submodule_search_locations:
            candidate = Path(package_dir) / "data" / "pretrained_model.yaml"
            if candidate.exists():
                return candidate

    return Path("pretrained_model.yaml")


def parse_scalar(value: str) -> Any:
    """Parse a small YAML scalar used in the registry."""
    stripped = value.strip()
    if stripped in {"", "null", "None"}:
        return None
    if stripped in {"true", "True"}:
        return True
    if stripped in {"false", "False"}:
        return False
    if (stripped.startswith('"') and stripped.endswith('"')) or (
        stripped.startswith("'") and stripped.endswith("'")
    ):
        return stripped[1:-1]
    try:
        return int(stripped)
    except ValueError:
        pass
    try:
        return float(stripped)
    except ValueError:
        return stripped


def parse_inline_list(value: str) -> Any:
    """Parse simple JSON-like inline lists/dicts from the registry."""
    text = value.strip()
    if not (text.startswith("[") or text.startswith("{")):
        return parse_scalar(text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(text)
        except (SyntaxError, ValueError):
            return text


def parse_registry(path: Path) -> dict[str, dict[str, Any]]:
    """Parse the registry fields needed for safe key inspection."""
    if not path.exists():
        raise FileNotFoundError(f"Registry file not found: {path}")

    entries: dict[str, dict[str, Any]] = {}
    current_key: str | None = None
    section: str | None = None
    subsection: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        entry_match = _ENTRY_RE.match(raw_line)
        if entry_match:
            current_key = entry_match.group(1)
            entries[current_key] = {}
            section = None
            subsection = None
            continue

        if current_key is None:
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = raw_line.strip()

        if indent == 4 and stripped.endswith(":"):
            section = stripped[:-1]
            subsection = None
            entries[current_key].setdefault(section, {})
            continue

        if indent == 8 and stripped.endswith(":") and section in {"architecture", "ioconfig"}:
            subsection = stripped[:-1]
            entries[current_key].setdefault(section, {}).setdefault(subsection, {})
            continue

        if ":" not in stripped:
            continue

        name, value = stripped.split(":", 1)
        name = name.strip()
        value = value.strip()

        if indent == 4:
            entries[current_key][name] = parse_inline_list(value)
        elif indent == 8 and section in {"architecture", "ioconfig"}:
            entries[current_key].setdefault(section, {})[name] = parse_inline_list(value)
        elif indent == 12 and section in {"architecture", "ioconfig"} and subsection:
            entries[current_key].setdefault(section, {}).setdefault(subsection, {})[name] = parse_inline_list(value)

    return entries


def summarize(entries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Build a compact registry summary."""
    architecture_classes = Counter(
        entry.get("architecture", {}).get("class", "<missing>")
        for entry in entries.values()
    )
    ioconfig_classes = Counter(
        entry.get("ioconfig", {}).get("class", "<missing>") for entry in entries.values()
    )
    datasets = Counter(entry.get("dataset", "<missing>") for entry in entries.values())
    hf_repos = Counter(entry.get("hf_repo_id", "<missing>") for entry in entries.values())
    return {
        "count": len(entries),
        "datasets": dict(datasets.most_common()),
        "architecture_classes": dict(architecture_classes.most_common()),
        "ioconfig_classes": dict(ioconfig_classes.most_common()),
        "hf_repos": dict(hf_repos.most_common()),
    }


def render_key(key: str, entry: dict[str, Any], *, show_ioconfig: bool) -> str:
    """Render one registry entry as a concise one-line summary."""
    arch = entry.get("architecture", {}).get("class", "<missing>")
    ioconfig = entry.get("ioconfig", {}).get("class", "<missing>")
    dataset = entry.get("dataset", "<missing>")
    repo = entry.get("hf_repo_id", "<missing>")
    line = f"{key}\tarchitecture={arch}\tioconfig={ioconfig}\tdataset={dataset}\thf_repo_id={repo}"
    if show_ioconfig:
        kwargs = entry.get("ioconfig", {}).get("kwargs", {})
        line += f"\tioconfig_kwargs={json.dumps(kwargs, sort_keys=True)}"
    return line


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Summarize TIAToolbox pretrained_model.yaml without imports, downloads, or network calls.",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=default_registry_path(),
        help="Path to pretrained_model.yaml. Defaults to the installed TIAToolbox package data; pass an explicit file for offline audits.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print aggregate counts for datasets, architecture classes, IO config classes, and repositories.",
    )
    parser.add_argument(
        "--list-prefix",
        metavar="PREFIX",
        help="List model keys beginning with PREFIX, case-insensitive, without loading weights.",
    )
    parser.add_argument(
        "--show-ioconfig",
        action="store_true",
        help="Include compact ioconfig kwargs for listed keys.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human-readable text.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        entries = parse_registry(args.registry)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    wants_summary = args.summary or not args.list_prefix
    result: dict[str, Any] = {}

    if wants_summary:
        result["summary"] = summarize(entries)

    if args.list_prefix:
        prefix = args.list_prefix.lower()
        matches = {
            key: entries[key]
            for key in sorted(entries)
            if key.lower().startswith(prefix)
        }
        result["matches"] = matches

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if "summary" in result:
        summary = result["summary"]
        print(f"model_count: {summary['count']}")
        for name in ["datasets", "architecture_classes", "ioconfig_classes", "hf_repos"]:
            print(f"{name}:")
            for key, value in summary[name].items():
                print(f"  {key}: {value}")

    if args.list_prefix:
        matches = result["matches"]
        print(f"matches_for_prefix: {args.list_prefix} ({len(matches)})")
        for key, entry in matches.items():
            print(render_key(key, entry, show_ioconfig=args.show_ioconfig))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
