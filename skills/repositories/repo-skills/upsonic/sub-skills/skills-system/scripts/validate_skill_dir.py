#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

DISCO_FRONTMATTER_FIELDS = {"disable-model-invocation", "disco-role"}


def _filter_disco_frontmatter_errors(errors: list[str]) -> list[str]:
    """Suppress Upsonic-validator errors caused only by DisCo repo-skill fields."""
    filtered: list[str] = []
    for error in errors:
        if not error.startswith("Unexpected fields in frontmatter:"):
            filtered.append(error)
            continue
        match = re.search(r"Unexpected fields in frontmatter: (.*?)\. Only", error)
        if match is None:
            filtered.append(error)
            continue
        extras = {item.strip() for item in match.group(1).split(",") if item.strip()}
        if extras - DISCO_FRONTMATTER_FIELDS:
            filtered.append(error)
    return filtered


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an Upsonic skill directory.")
    parser.add_argument("skill_dir", type=Path)
    parser.add_argument(
        "--allow-disco-fields",
        action="store_true",
        help="Allow DisCo repo-skill frontmatter fields such as disable-model-invocation and metadata.disco-role.",
    )
    args = parser.parse_args()

    from upsonic.skills.validator import validate_skill_directory

    errors = validate_skill_directory(args.skill_dir)
    if args.allow_disco_fields:
        errors = _filter_disco_frontmatter_errors(errors)

    if errors:
        for error in errors:
            print(error)
        return 1

    suffix = " (with DisCo fields allowed)" if args.allow_disco_fields else ""
    print(f"{args.skill_dir}: valid{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
