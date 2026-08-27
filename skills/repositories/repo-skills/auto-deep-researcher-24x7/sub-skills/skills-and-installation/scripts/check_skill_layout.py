#!/usr/bin/env python3
"""Read-only checker for the eight source skills and nested active roots.

The checker deliberately inspects only immediate children of a source skills
root. A directory containing its own SKILL.md is reported as an active root,
not merged into the source set.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EXPECTED = {
    "auto-experiment",
    "conf-search",
    "daily-papers",
    "experiment-status",
    "gpu-monitor",
    "obsidian-sync",
    "paper-analyze",
    "progress-report",
}
ALLOWED_SOURCE_KEYS = {"name", "description", "license", "allowed-tools", "metadata"}
KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s|$)")


def _frontmatter_keys(path: Path) -> tuple[set[str], str | None]:
    """Return top-level keys and a short error, without importing YAML."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return set(), "missing opening YAML delimiter"
    end = text.find("\n---\n", 4)
    if end < 0:
        return set(), "missing closing YAML delimiter"

    keys: set[str] = set()
    for line in text[4:end].splitlines():
        if not line or line[0].isspace() or line.lstrip().startswith("#"):
            continue
        match = KEY_RE.match(line)
        if match:
            keys.add(match.group(1))
    return keys, None


def _skills_root(root: Path) -> Path:
    if (root / "SKILL.md").is_file():
        return root
    if (root / "skills").is_dir():
        return root / "skills"
    return root


def _report_active_root(root: Path) -> int:
    skill_file = root / "SKILL.md"
    failures: list[str] = []
    if skill_file.is_file():
        keys, error = _frontmatter_keys(skill_file)
        if error:
            failures.append(error)
        else:
            missing = sorted({"name", "description"} - keys)
            if missing:
                failures.append("missing " + ", ".join(missing))
    else:
        failures.append("missing root SKILL.md (staged active root)")

    print(f"ACTIVE_ROOT (not merged): {root}")
    subskills_root = root / "sub-skills"
    children = sorted(
        child for child in subskills_root.iterdir()
        if subskills_root.is_dir() and child.is_dir()
    ) if subskills_root.is_dir() else []
    if children:
        print("  direct sub-skills (kept under this root):")
        for child in children:
            marker = "SKILL.md" if (child / "SKILL.md").is_file() else "MISSING SKILL.md"
            print(f"    - {child.name} [{marker}]")
            if marker != "SKILL.md":
                failures.append(f"{child.name}: missing SKILL.md")
    else:
        print("  direct sub-skills: none")
    if failures:
        print("  FAILURES:")
        for failure in failures:
            print(f"    - {failure}")
        return 1
    return 0


def check(root: Path) -> int:
    root = root.expanduser().resolve()
    if not root.is_dir():
        print(f"ERROR: root is not a directory: {root}")
        return 2

    if (root / "SKILL.md").is_file() or (root / "sub-skills").is_dir():
        return _report_active_root(root)

    skills_root = _skills_root(root)
    if not skills_root.is_dir():
        print(f"ERROR: skills root is not a directory: {skills_root}")
        return 2

    # Only immediate children are source candidates. In particular, do not
    # recursively fold skills/disco or any other generated graph into them.
    candidates = sorted(
        child for child in skills_root.iterdir()
        if child.is_dir() and (child / "SKILL.md").is_file()
    )
    names = {child.name for child in candidates}
    failures: list[str] = []

    missing = sorted(EXPECTED - names)
    unexpected = sorted(names - EXPECTED)
    if missing:
        failures.append("missing source skills: " + ", ".join(missing))
    if unexpected:
        failures.append("unexpected immediate source skills: " + ", ".join(unexpected))

    for child in candidates:
        keys, error = _frontmatter_keys(child / "SKILL.md")
        if error:
            failures.append(f"{child.name}: {error}")
            continue
        if "name" not in keys or "description" not in keys:
            failures.append(f"{child.name}: frontmatter needs name and description")
        bad_keys = sorted(keys - ALLOWED_SOURCE_KEYS)
        if bad_keys:
            failures.append(f"{child.name}: unsupported source keys: {', '.join(bad_keys)}")

    print(f"SOURCE_ROOT: {skills_root}")
    print(f"IMMEDIATE_SOURCE_SKILLS: {len(candidates)}")
    for child in candidates:
        print(f"  - {child.name}")

    nested_parent = skills_root / "disco"
    nested = []
    if nested_parent.is_dir():
        nested = sorted(
            child for child in nested_parent.iterdir()
            if child.is_dir() and (
                (child / "SKILL.md").is_file() or (child / "sub-skills").is_dir()
            )
        )
    if nested:
        print("NESTED_ACTIVE_ROOTS (not merged):")
        for child in nested:
            state = "complete" if (child / "SKILL.md").is_file() else "staged"
            print(f"  - {child} [{state}]")

    if failures:
        print("FAILURES:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("OK: eight immediate source skills are present and readable")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only check of source skill layout and nested active roots"
    )
    parser.add_argument(
        "--root",
        default=".",
        help="repository root, skills root, or one active generated root",
    )
    args = parser.parse_args()
    return check(Path(args.root))


if __name__ == "__main__":
    sys.exit(main())
