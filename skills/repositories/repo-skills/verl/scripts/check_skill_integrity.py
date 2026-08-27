#!/usr/bin/env python3
"""Static integrity checks for the bundled verl repo skill."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PRIVATE_PATTERNS = tuple(
    [
        "/" + "root" + "/",
        "/" + "share" + "/",
        "github" + "-repos",
        ".disco" + "/agent/envs",
        "conda" + "-prefix",
        "repo_env" + "_report.json",
    ]
)
REQUIRED_ROOT_FILES = (
    "SKILL.md",
    "references/repo-provenance.md",
    "references/troubleshooting.md",
)
REQUIRED_SUBSKILLS = (
    "setup-and-backends",
    "data-and-rewards",
    "training-and-configs",
    "rollout-and-tools",
    "checkpoints-and-model-ops",
    "repo-development",
)
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the self-contained verl skill tree for common publication issues.")
    parser.add_argument("skill_dir", nargs="?", type=Path, default=Path.cwd(), help="Skill root directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    return parser.parse_args()


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def frontmatter_name(path: Path) -> str | None:
    text = read_text(path)
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    for line in text[4:end].splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip('"\'')
    return None


def check_links(path: Path, root: Path) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    text = read_text(path)
    for match in LINK_RE.finditer(text):
        target = match.group(1).split("#", 1)[0]
        if not target or re.match(r"^[a-z]+://", target) or target.startswith("mailto:"):
            continue
        if target.startswith("/"):
            issues.append({"file": rel(path, root), "issue": "absolute-link", "target": target})
            continue
        resolved = (path.parent / target).resolve()
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            issues.append({"file": rel(path, root), "issue": "outside-skill-link", "target": target})
            continue
        if not resolved.exists():
            issues.append({"file": rel(path, root), "issue": "missing-link-target", "target": target})
    return issues


def main() -> int:
    args = parse_args()
    root = args.skill_dir.resolve()
    issues: list[dict[str, Any]] = []

    for required in REQUIRED_ROOT_FILES:
        if not (root / required).is_file():
            issues.append({"file": required, "issue": "missing-required-root-file"})

    root_name = frontmatter_name(root / "SKILL.md") if (root / "SKILL.md").exists() else None
    if root_name != "verl":
        issues.append({"file": "SKILL.md", "issue": "root-frontmatter-name", "value": root_name})

    for subskill in REQUIRED_SUBSKILLS:
        skill_md = root / "sub-skills" / subskill / "SKILL.md"
        if not skill_md.is_file():
            issues.append({"file": rel(skill_md, root), "issue": "missing-subskill-skill-md"})
            continue
        name = frontmatter_name(skill_md)
        if name != subskill:
            issues.append({"file": rel(skill_md, root), "issue": "subskill-frontmatter-name", "expected": subskill, "value": name})

    for path in root.rglob("*"):
        if path.name == "__pycache__" or path.suffix == ".pyc":
            issues.append({"file": rel(path, root), "issue": "generated-python-cache"})
        if path.is_file() and path.suffix in {".md", ".py", ".sh", ".yaml", ".yml", ".json"}:
            text = read_text(path)
            for pattern in PRIVATE_PATTERNS:
                if pattern in text:
                    issues.append({"file": rel(path, root), "issue": "private-or-artifact-path-leak", "pattern": pattern})
            if path.suffix == ".md":
                issues.extend(check_links(path, root))

    result = {"ok": not issues, "issue_count": len(issues), "issues": issues}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        if result["ok"]:
            print("OK: skill integrity checks passed")
        else:
            print(f"FAIL: {len(issues)} issue(s)")
            for issue in issues:
                print(json.dumps(issue, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
