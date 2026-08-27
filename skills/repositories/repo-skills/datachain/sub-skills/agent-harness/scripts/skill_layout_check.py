#!/usr/bin/env python3
"""Print DataChain agent-skill target directories without mutating files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Kept in sync with the public DataChain CLI contract so --help works even when
# the helper is launched with the wrong Python interpreter. Actual layout data is
# loaded from datachain.cli.commands.skill.TARGET_LAYOUT at runtime.
TARGET_NAMES = ("claude", "cursor", "codex", "copilot", "pi")
SKILL_NAMES = ("core", "knowledge", "jobs")


def load_cli_layout() -> tuple[tuple[str, ...], dict[str, dict[str, Any]]]:
    """Import DataChain's authoritative skill CLI layout."""
    try:
        from datachain.cli.commands.skill import SKILLS, TARGET_LAYOUT
    except Exception as exc:  # pragma: no cover - exercised when datachain is absent
        print(
            "error: could not import datachain.cli.commands.skill.TARGET_LAYOUT: "
            f"{exc}",
            file=sys.stderr,
        )
        print(
            "Install DataChain or run this helper with the Python environment that "
            "provides the `datachain` CLI.",
            file=sys.stderr,
        )
        sys.exit(2)
    return tuple(SKILLS), TARGET_LAYOUT


def _mode_value(layout: dict[str, Any], key: str, local: bool) -> str | None:
    local_key = f"{key}_local"
    if local and layout.get(local_key) is not None:
        return layout[local_key]
    return layout[key]


def resolve_target(
    target: str, *, local: bool, skills: tuple[str, ...], layouts: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Return resolved directories and command behavior for one target."""
    layout = layouts[target]
    base = Path.cwd() if local else Path.home()
    skills_dir_rel = _mode_value(layout, "skills_dir", local)
    commands_dir_rel = _mode_value(layout, "commands_dir", local)
    command_ext = layout.get("command_ext")
    writes_commands = (
        commands_dir_rel is not None
        and command_ext is not None
        and (local or not layout.get("commands_local_only", False))
    )
    return {
        "target": target,
        "scope": "local" if local else "global",
        "base": str(base),
        "skills_dir": str(base / skills_dir_rel),
        "commands_dir": str(base / commands_dir_rel)
        if writes_commands and commands_dir_rel
        else None,
        "writes_commands": writes_commands,
        "command_ext": command_ext if writes_commands else None,
        "command_file_pattern": f"datachain-<skill>{command_ext}"
        if writes_commands and command_ext
        else None,
        "valid_skills": list(skills),
    }


def print_human(record: dict[str, Any]) -> None:
    print(f"Target: {record['target']}")
    print(f"Scope: {record['scope']}")
    print(f"Base: {record['base']}")
    print(f"Skills directory: {record['skills_dir']}")
    if record["writes_commands"]:
        print(f"Command/rule directory: {record['commands_dir']}")
        print(f"Command/rule filename: {record['command_file_pattern']}")
    else:
        print("Command/rule directory: (none for this target/scope)")
    print("Valid skills: " + ", ".join(record["valid_skills"]))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Resolve DataChain `datachain skill install` target directories "
            "without creating, deleting, or modifying files."
        )
    )
    parser.add_argument(
        "--target",
        choices=sorted(TARGET_NAMES),
        default="claude",
        help="Target AI coding tool to inspect (default: claude).",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Resolve project-local directories from the current working directory.",
    )
    parser.add_argument(
        "--all-targets",
        action="store_true",
        help="Print layouts for all supported targets instead of only --target.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    skills, layouts = load_cli_layout()
    targets = sorted(layouts.keys()) if args.all_targets else [args.target]
    records = [
        resolve_target(target, local=args.local, skills=skills, layouts=layouts)
        for target in targets
    ]
    if args.json:
        print(json.dumps(records if args.all_targets else records[0], indent=2))
    else:
        for idx, record in enumerate(records):
            if idx:
                print()
            print_human(record)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
