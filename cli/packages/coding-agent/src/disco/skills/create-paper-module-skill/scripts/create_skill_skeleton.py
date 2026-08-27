#!/usr/bin/env python3
"""Create a minimal DisCo operating skill skeleton."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-") or "skill"


def quote_yaml_string(value: str) -> str:
    escaped = value.strip().replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir", help="Directory to create.")
    parser.add_argument("--name", required=True, help="Skill name.")
    parser.add_argument("--description", required=True, help="Skill trigger description.")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).expanduser().resolve()
    name = slugify(args.name)
    if len(name) > 64:
        parser.error("canonicalized --name must be at most 64 characters")
    if skill_dir.name != name:
        parser.error(f"skill_dir basename must match canonicalized --name: {name}")
    (skill_dir / "scripts").mkdir(parents=True, exist_ok=True)
    (skill_dir / "tests").mkdir(parents=True, exist_ok=True)
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        skill_md.write_text(
            "\n".join(
                [
                    "---",
                    f"name: {name}",
                    f"description: {quote_yaml_string(args.description)}",
                    "metadata:",
                    "  disco-role: operating",
                    "---",
                    "",
                    f"# {name.replace('-', ' ').title()}",
                    "",
                    "Use this skill when ...",
                    "",
                    "## Inputs",
                    "",
                    "## Outputs",
                    "",
                    "## Workflow",
                    "",
                    "## Validation",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    print(skill_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
