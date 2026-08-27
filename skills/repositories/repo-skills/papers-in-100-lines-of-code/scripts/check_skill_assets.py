#!/usr/bin/env python3
"""Validate basic integrity of the bundled repo skill assets.

The check is stdlib-only and limited to the generated skill directory. It does
not read the original repository checkout and does not execute paper code.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REQUIRED_SUBSKILLS = [
    "paper-catalog-and-execution",
    "generative-models",
    "neural-rendering-3d",
    "optimization-meta-rl",
]


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError(f"{path} missing YAML frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise AssertionError(f"{path} frontmatter is not closed")
    fm = text[4:end]
    data = {}
    for line in fm.splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip('"')
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate generated Papers-in-100-Lines skill assets.")
    parser.add_argument("--skill-dir", type=Path, default=Path(__file__).resolve().parents[1], help="Generated skill directory")
    args = parser.parse_args()
    skill_dir = args.skill_dir.resolve()

    root_skill = skill_dir / "SKILL.md"
    if not root_skill.exists():
        raise AssertionError("root SKILL.md is missing")
    root_fm = parse_frontmatter(root_skill)
    if root_fm.get("name") != skill_dir.name:
        raise AssertionError("root frontmatter name does not match directory")
    if root_fm.get("disable-model-invocation") != "true":
        raise AssertionError("root SKILL.md must disable direct model invocation")

    index_path = skill_dir / "references" / "implementation-index.json"
    data = json.loads(index_path.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    if len(entries) != 62:
        raise AssertionError(f"expected 62 catalog entries, found {len(entries)}")
    owners = {entry.get("owner_sub_skill") for entry in entries}
    missing = set(REQUIRED_SUBSKILLS[1:]) - owners
    if missing:
        raise AssertionError(f"catalog missing owner groups: {sorted(missing)}")

    for subskill in REQUIRED_SUBSKILLS:
        path = skill_dir / "sub-skills" / subskill / "SKILL.md"
        if not path.exists():
            raise AssertionError(f"missing sub-skill {subskill}")
        fm = parse_frontmatter(path)
        if fm.get("name") != subskill:
            raise AssertionError(f"{path} frontmatter name mismatch")
        if fm.get("disable-model-invocation") != "true":
            raise AssertionError(f"{path} must disable direct model invocation")
        text = path.read_text(encoding="utf-8")
        for link in re.findall(r"\(([^)]+)\)", text):
            if link.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = (path.parent / link).resolve()
            if not str(target).startswith(str(skill_dir)):
                raise AssertionError(f"{path} has out-of-tree link: {link}")
            if not target.exists():
                raise AssertionError(f"{path} has missing link target: {link}")

    print(f"OK: {skill_dir} has {len(entries)} catalog entries and {len(REQUIRED_SUBSKILLS)} sub-skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
