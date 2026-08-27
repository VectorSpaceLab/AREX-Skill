#!/usr/bin/env python3
"""Check generated LeRobot runtime Markdown links and required frontmatter.

This checker is intentionally independent of the source checkout. It rejects
links that escape the generated skill directory or point at missing files.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
REQUIRED_MARKERS = (
    "disable-model-invocation: true",
    "disco-role: operating",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate links and metadata in a generated skill tree.")
    parser.add_argument("root", type=Path, nargs="?", default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    errors: list[str] = []
    skill_files = sorted(root.rglob("SKILL.md"))
    if not skill_files:
        errors.append(f"no SKILL.md files found under {root}")

    for path in skill_files:
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            errors.append(f"{path.relative_to(root)}: missing YAML frontmatter")
        for marker in REQUIRED_MARKERS:
            if marker not in text:
                errors.append(f"{path.relative_to(root)}: missing `{marker}`")
        for raw_target in LINK_RE.findall(text):
            target = raw_target.split("#", 1)[0].strip()
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(root)
            except ValueError:
                errors.append(f"{path.relative_to(root)}: link escapes skill root: {raw_target}")
                continue
            if not resolved.exists():
                errors.append(f"{path.relative_to(root)}: missing link target: {raw_target}")

    if errors:
        print("FAIL")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print(f"PASS: {len(skill_files)} SKILL.md files and all local links are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
