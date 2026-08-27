#!/usr/bin/env python3
"""Lightweight preflight for one Scientific Agent Skills package.

This helper intentionally uses only the Python standard library and never
imports skill code. It catches common repository mistakes before heavier CI
checks such as `skills-ref validate` and `tests/_meta`.

Example:
    python audit_skill_frontmatter.py --skill-dir skills/scanpy
    python audit_skill_frontmatter.py --skill-dir skills/scanpy --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ALLOWED_FIELDS = {"name", "description", "license", "compatibility", "allowed-tools", "metadata"}
MAX_LINES = 500
INLINE_PATH = re.compile(r"`((?:assets|references|scripts)/[A-Za-z0-9_./-]+)`")
MARKDOWN_LINK = re.compile(r"\]\(((?:assets|references|scripts)/[A-Za-z0-9_./-]+)\)")


def frontmatter(text: str) -> tuple[str | None, list[str]]:
    if not text.startswith("---\n"):
        return None, ["SKILL.md must start with YAML frontmatter delimited by ---"]
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, ["frontmatter closing delimiter must be --- on its own line"]
    return text[4:end], []


def top_level_entries(fm: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for line in fm.splitlines():
        match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):(.*)$", line)
        if match:
            entries.append((match.group(1), match.group(2).strip()))
    return entries


def metadata_scalar_lines(fm: str) -> dict[str, str]:
    lines = fm.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.startswith("metadata:"))
    except StopIteration:
        return {}
    scalars: dict[str, str] = {}
    for line in lines[start + 1 :]:
        if line.strip() and not line.startswith((" ", "\t")):
            break
        match = re.match(r"^  ([A-Za-z][A-Za-z0-9_-]*):(.*)$", line)
        if match and match.group(2).strip():
            scalars[match.group(1)] = match.group(2).strip()
    return scalars


def is_quoted(raw: str) -> bool:
    raw = raw.strip()
    return len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {'"', "'"}


def local_link_problems(skill_dir: Path, documents: list[Path]) -> list[str]:
    problems: list[str] = []
    for doc in documents:
        if not doc.is_file():
            continue
        for number, line in enumerate(doc.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for relative in sorted(set(INLINE_PATH.findall(line)) | set(MARKDOWN_LINK.findall(line))):
                if not (skill_dir / relative).exists():
                    problems.append(f"{doc.relative_to(skill_dir)}:{number}: referenced `{relative}` does not exist")
    return problems


def audit(skill_dir: Path) -> list[str]:
    problems: list[str] = []
    skill_dir = skill_dir.resolve()
    md = skill_dir / "SKILL.md"
    if not skill_dir.is_dir():
        return [f"not a directory: {skill_dir}"]
    if not md.is_file():
        return [f"missing SKILL.md under {skill_dir}"]

    text = md.read_text(encoding="utf-8", errors="replace")
    fm, fm_problems = frontmatter(text)
    problems.extend(fm_problems)
    if fm is not None:
        entries = top_level_entries(fm)
        values = dict(entries)
        keys = [key for key, _ in entries]
        for required in ("name", "description", "metadata"):
            if required not in keys:
                problems.append(f"frontmatter missing `{required}`")
        for key in keys:
            if key not in ALLOWED_FIELDS:
                problems.append(f"top-level `{key}` is not a canonical Agent Skills field")
        name = values.get("name", "").strip("'\"")
        if name and name != skill_dir.name:
            problems.append(f"frontmatter name `{name}` must equal directory name `{skill_dir.name}`")
        for key, value in entries:
            if value.startswith(("{", "[")):
                problems.append(f"`{key}` uses JSON flow style; use block YAML")
        allowed_tools = values.get("allowed-tools")
        if allowed_tools is not None and ("," in allowed_tools or allowed_tools.startswith("[")):
            problems.append("allowed-tools must be a space-separated string, not a list or comma-separated value")
        metadata = metadata_scalar_lines(fm)
        version = metadata.get("version")
        if version is None:
            problems.append("metadata.version is required")
        elif not is_quoted(version):
            problems.append("metadata.version must be quoted, for example version: \"1.0\"")
        for key, value in metadata.items():
            if key == "version":
                continue
            ambiguous = re.fullmatch(r"\d+|\d+\.\d+|true|false|yes|no|on|off|\d{4}-\d{2}-\d{2}", value, re.I)
            if ambiguous and not is_quoted(value):
                problems.append(f"metadata.{key} should be quoted to stay a string")

    line_count = len(text.splitlines())
    if line_count > MAX_LINES:
        problems.append(f"SKILL.md has {line_count} lines; keep it at or below {MAX_LINES}")

    for path in sorted(skill_dir.rglob("*")):
        rel = path.relative_to(skill_dir)
        if path.is_dir() and path.name == "tests":
            problems.append(f"ships tests directory `{rel}`; tests belong under repository-level tests/{skill_dir.name}/")
        if path.is_file() and path.name.startswith("test_") and path.suffix == ".py":
            problems.append(f"ships test file `{rel}`; tests belong under repository-level tests/{skill_dir.name}/")
        if path.suffix in {".pyc", ".pyo"} or path.name == "__pycache__":
            problems.append(f"ships bytecode/cache artifact `{rel}`")

    docs = [md]
    refs = skill_dir / "references"
    if refs.is_dir():
        docs.extend(sorted(refs.glob("*.md")))
    problems.extend(local_link_problems(skill_dir, docs))
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-dir", required=True, help="Path to one skill directory containing SKILL.md")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args(argv)

    skill_dir = Path(args.skill_dir)
    problems = audit(skill_dir)
    status = "pass" if not problems else "fail"
    if args.json:
        print(json.dumps({"status": status, "skill_dir": str(skill_dir), "problems": problems}, indent=2))
    else:
        if problems:
            print(f"FAIL {skill_dir}")
            for problem in problems:
                print(f"- {problem}")
        else:
            print(f"PASS {skill_dir}")
    if problems and any(problem.startswith("missing SKILL.md") or problem.startswith("not a directory") for problem in problems):
        return 2
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
