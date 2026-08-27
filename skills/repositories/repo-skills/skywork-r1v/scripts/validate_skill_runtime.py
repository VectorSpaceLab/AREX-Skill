#!/usr/bin/env python3
"""Validate the generated Skywork-R1V runtime tree.

This helper performs light structural checks only:
- root and sub-skill SKILL.md frontmatter names
- operating-role frontmatter markers
- obvious runtime path leaks in Markdown files
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT_ID = "skywork-r1v"
SKILL_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
NAME_RE = re.compile(r"^name:\s*([A-Za-z0-9-]+)\s*$", re.MULTILINE)
ROLE_RE = re.compile(r"^\s*disco-role:\s*operating\s*$", re.MULTILINE)
DISABLE_RE = re.compile(r"^disable-model-invocation:\s*true\s*$", re.MULTILINE)
LINK_RE = re.compile(r"\]\(([^)]+)\)")
BAD_TEXT_PATTERNS = [
    "/root/github-repos/",
    "/root/.disco/",
    "production_batches/",
    "skills/tests/",
]


def _frontmatter(text: str) -> str:
    match = SKILL_FRONTMATTER_RE.match(text)
    if not match:
        return ""
    return match.group(1)


def _check_skill_md(path: Path, expected_name: str) -> List[str]:
    issues: List[str] = []
    text = path.read_text(encoding="utf-8")
    block = _frontmatter(text)
    if not block:
        issues.append("missing YAML frontmatter")
        return issues

    name_match = NAME_RE.search(block)
    if not name_match:
        issues.append("missing frontmatter name")
    elif name_match.group(1) != expected_name:
        issues.append(f"frontmatter name {name_match.group(1)!r} != {expected_name!r}")

    if not DISABLE_RE.search(block):
        issues.append("missing disable-model-invocation: true")
    if not ROLE_RE.search(block):
        issues.append("missing metadata.disco-role: operating")

    return issues


def _scan_markdown(path: Path, root: Path) -> List[str]:
    issues: List[str] = []
    if path.name == "repo-provenance.md":
        return issues
    text = path.read_text(encoding="utf-8")

    for match in LINK_RE.finditer(text):
        target = match.group(1).strip().strip("<>")
        if not target or target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        link_path = target.split("#", 1)[0].split("?", 1)[0]
        if not link_path:
            continue
        resolved = (path.parent / link_path).resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            issues.append(f"contains Markdown link outside generated tree: {target}")

    for pattern in BAD_TEXT_PATTERNS:
        if pattern in text:
            issues.append(f"contains suspicious path text: {pattern}")
    return issues


def validate(root: Path) -> Dict[str, object]:
    issues: List[Dict[str, str]] = []
    checked = 0

    root_skill = root / "SKILL.md"
    if root_skill.exists():
        checked += 1
        for issue in _check_skill_md(root_skill, ROOT_ID):
            issues.append({"file": str(root_skill), "issue": issue})
    else:
        issues.append({"file": str(root_skill), "issue": "missing root SKILL.md"})

    subskills_root = root / "sub-skills"
    if subskills_root.exists():
        for subskill in sorted(p for p in subskills_root.iterdir() if p.is_dir()):
            skill_file = subskill / "SKILL.md"
            if skill_file.exists():
                checked += 1
                for issue in _check_skill_md(skill_file, subskill.name):
                    issues.append({"file": str(skill_file), "issue": issue})
            else:
                issues.append({"file": str(skill_file), "issue": "missing sub-skill SKILL.md"})

    for path in root.rglob("*.md"):
        if path.name == "SKILL.md":
            continue
        for issue in _scan_markdown(path, root):
            issues.append({"file": str(path), "issue": issue})

    return {
        "root": str(root),
        "checked_skill_files": checked,
        "issue_count": len(issues),
        "issues": issues,
        "ok": not issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the generated Skywork-R1V runtime tree.")
    parser.add_argument("--root", default=".", help="Path to the generated skywork-r1v skill directory.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of human output.")
    args = parser.parse_args()

    summary = validate(Path(args.root).resolve())
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"Checked {summary['checked_skill_files']} SKILL.md files")
        print(f"Issues: {summary['issue_count']}")
        for item in summary["issues"]:
            print(f"- {item['file']}: {item['issue']}")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
