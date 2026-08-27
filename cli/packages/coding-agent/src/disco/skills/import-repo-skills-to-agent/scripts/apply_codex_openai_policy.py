#!/usr/bin/env python3
"""Add Codex implicit-invocation policy files to imported repo skills.

This script is intentionally target-side only. It is used by the
import-repo-skills-to-agent workflow after copying selected DisCo repo skills
into a Codex skills root, so the source managed library remains unchanged.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROUTER_ID = "repo-skills-router"
OPENAI_POLICY = "policy:\n  allow_implicit_invocation: false\n"
ALLOW_IMPLICIT_LINE = "  allow_implicit_invocation: false"


def is_top_level_key(line: str) -> bool:
    return bool(re.match(r"^[A-Za-z0-9_-]+\s*:", line))


def set_allow_implicit_invocation_false(text: str) -> str:
    lines = text.splitlines()

    policy_index = None
    for index, line in enumerate(lines):
        if re.match(r"^policy\s*:", line):
            policy_index = index
            break

    if policy_index is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend(["policy:", ALLOW_IMPLICIT_LINE])
        return "\n".join(lines) + "\n"

    if lines[policy_index].strip() != "policy:":
        lines[policy_index] = "policy:"

    policy_end = len(lines)
    for index in range(policy_index + 1, len(lines)):
        if is_top_level_key(lines[index]):
            policy_end = index
            break

    for index in range(policy_index + 1, policy_end):
        if re.match(r"^\s*allow_implicit_invocation\s*:", lines[index]):
            lines[index] = ALLOW_IMPLICIT_LINE
            return "\n".join(lines) + "\n"

    lines.insert(policy_index + 1, ALLOW_IMPLICIT_LINE)
    return "\n".join(lines) + "\n"


def iter_skill_files(skill_dir: Path) -> list[Path]:
    files = [
        path
        for path in skill_dir.rglob("SKILL.md")
        if not any(part.startswith(".") or part == "node_modules" for part in path.relative_to(skill_dir).parts)
    ]
    return sorted(files)


def apply_policy(skill_dir: Path) -> list[Path]:
    written: list[Path] = []
    if skill_dir.name == ROUTER_ID:
        return written
    for skill_file in iter_skill_files(skill_dir):
        agents_dir = skill_file.parent / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        openai_yaml = agents_dir / "openai.yaml"
        if openai_yaml.exists():
            updated = set_allow_implicit_invocation_false(openai_yaml.read_text(encoding="utf-8"))
        else:
            updated = OPENAI_POLICY
        openai_yaml.write_text(updated, encoding="utf-8")
        written.append(openai_yaml)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill agents/openai.yaml for Codex-imported non-router repo skills.",
    )
    parser.add_argument(
        "skill_dirs",
        nargs="+",
        help="Target skill directories that were copied or overwritten in the Codex skills root.",
    )
    args = parser.parse_args()

    all_written: list[Path] = []
    for raw in args.skill_dirs:
        skill_dir = Path(raw).expanduser().resolve()
        if not skill_dir.is_dir():
            raise SystemExit(f"not a directory: {skill_dir}")
        all_written.extend(apply_policy(skill_dir))

    for path in all_written:
        print(path)
    print(f"codex openai policy files written: {len(all_written)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
