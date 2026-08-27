#!/usr/bin/env python3
"""Check basic structural readiness of the generated InternGPT repo skill.

This validator is intentionally shallow and self-contained:
- it does not import any InternGPT modules
- it does not require PyYAML or other third-party packages
- it checks frontmatter, required files, local markdown links, and obvious
  path leaks that would break portability of the generated skill tree

Usage:
  python scripts/check_static_skill_readiness.py --skill-root .
  python scripts/check_static_skill_readiness.py --skill-root skills/disco/intern-gpt --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_ROOT_FILES = [
    "SKILL.md",
    "references/repo-provenance.md",
    "references/repo-routing-metadata.json",
    "references/troubleshooting.md",
]

REQUIRED_SUBSKILLS = [
    "app-deployment",
    "visual-dialogue-tools",
    "cross-modal-generation",
    "video-understanding",
]

LEAK_PATTERNS = (
    re.compile("/" + "root" + "/" + "github-repos" + "/"),
    re.compile("~/" + ".disco" + "/"),
    re.compile("skills/" + "tests" + "/"),
)

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


class ReadinessError(Exception):
    pass


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_frontmatter(text: str, path: Path) -> tuple[str, str, str, str]:
    if not text.startswith("---\n"):
        raise ReadinessError(f"{path} is missing YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ReadinessError(f"{path} has an unterminated YAML frontmatter block")
    frontmatter = text[4:end]
    body = text[end + 5 :]
    name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.M)
    desc_match = re.search(r'^description:\s*"([^"]+)"\s*$', frontmatter, re.M)
    role_match = re.search(r"^\s*disco-role:\s*operating\s*$", frontmatter, re.M)
    disable_match = re.search(r"^disable-model-invocation:\s*true\s*$", frontmatter, re.M)
    if not name_match:
        raise ReadinessError(f"{path} frontmatter is missing name")
    if not desc_match:
        raise ReadinessError(f"{path} frontmatter description must be double-quoted on one line")
    if not role_match:
        raise ReadinessError(f"{path} frontmatter is missing metadata.disco-role: operating")
    if not disable_match:
        raise ReadinessError(f"{path} frontmatter is missing disable-model-invocation: true")
    return name_match.group(1).strip().strip('"'), desc_match.group(1).strip(), frontmatter, body


def check_links(path: Path, text: str, root: Path, issues: list[str]) -> None:
    for target in LINK_RE.findall(text):
        target = target.strip()
        if not target or target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        clean = target.split("#", 1)[0]
        if not clean:
            continue
        resolved = (path.parent / clean).resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            issues.append(f"{path.relative_to(root)} links outside skill root: {target}")
            continue
        if not resolved.exists():
            issues.append(f"{path.relative_to(root)} links to missing file: {target}")


def check_text_for_leaks(path: Path, text: str, issues: list[str]) -> None:
    for pattern in LEAK_PATTERNS:
        if pattern.search(text):
            issues.append(f"{path} contains a private or review-artifact path leak: {pattern.pattern}")


def validate(root: Path) -> list[str]:
    issues: list[str] = []
    root = root.resolve()
    if not root.exists():
        return [f"skill root does not exist: {root}"]

    for rel in REQUIRED_ROOT_FILES:
        file_path = root / rel
        if not file_path.exists():
            issues.append(f"missing required file: {rel}")

    root_skill = root / "SKILL.md"
    if root_skill.exists():
        text = read_text(root_skill)
        name, _, _, body = parse_frontmatter(text, root_skill)
        if name != root.name:
            issues.append(f"root SKILL.md name {name!r} does not match directory basename {root.name!r}")
        check_links(root_skill, body, root, issues)
        check_text_for_leaks(root_skill, text, issues)

    subskills_root = root / "sub-skills"
    found = []
    if subskills_root.exists():
        for subdir in sorted(p for p in subskills_root.iterdir() if p.is_dir()):
            found.append(subdir.name)
            skill_md = subdir / "SKILL.md"
            if not skill_md.exists():
                issues.append(f"missing sub-skill SKILL.md: sub-skills/{subdir.name}/SKILL.md")
                continue
            text = read_text(skill_md)
            name, _, _, body = parse_frontmatter(text, skill_md)
            if name != subdir.name:
                issues.append(
                    f"sub-skill name mismatch in {skill_md.relative_to(root)}: frontmatter {name!r} != directory {subdir.name!r}"
                )
            check_links(skill_md, body, root, issues)
            check_text_for_leaks(skill_md, text, issues)

            # Required bundled folders for a sub-skill.
            if not (subdir / "references").exists():
                issues.append(f"missing sub-skill references directory: sub-skills/{subdir.name}/references")
            if not (subdir / "scripts").exists():
                issues.append(f"missing sub-skill scripts directory: sub-skills/{subdir.name}/scripts")
    else:
        issues.append("missing sub-skills directory")

    for required in REQUIRED_SUBSKILLS:
        if required not in found:
            issues.append(f"missing expected sub-skill directory: {required}")

    routing_path = root / "references/repo-routing-metadata.json"
    if routing_path.exists():
        try:
            routing = json.loads(read_text(routing_path))
        except Exception as exc:
            issues.append(f"repo-routing-metadata.json is not valid JSON: {exc}")
        else:
            if routing.get("skills", {}).get(root.name) is None:
                issues.append(f"routing metadata does not include skill id {root.name!r}")
    
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", default=".", help="Path to the generated skill root directory.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args(argv)

    root = Path(args.skill_root)
    issues = validate(root)
    ok = not issues

    if args.json:
        print(json.dumps({"ok": ok, "issues": issues}, indent=2))
    else:
        if ok:
            print(f"OK: {root.resolve()} looks structurally ready")
        else:
            print(f"FAILED: {len(issues)} issue(s)")
            for item in issues:
                print(f"- {item}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
