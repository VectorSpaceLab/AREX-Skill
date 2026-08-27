#!/usr/bin/env python3
"""Plan focused validation commands for one skill in a repository checkout.

The script does not run tests, install packages, or access the network. It
inspects the target checkout and reports the smallest useful command sequence.

Example:
    python plan_skill_checks.py --repo-root /work/scientific-agent-skills --skill scanpy
    python plan_skill_checks.py --repo-root . --skill scanpy --changed-kind shared --json
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path


def load_manifest(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return {"_error": str(exc)}


def plan(repo_root: Path, skill: str, changed_kind: str) -> tuple[dict, int]:
    if not repo_root.is_dir():
        return {"status": "error", "problems": [f"repo root does not exist: {repo_root}"]}, 2
    if not skill or "/" in skill or "\\" in skill:
        return {"status": "error", "problems": ["skill must be a single directory name"]}, 2

    skill_dir = repo_root / "skills" / skill
    skill_md = skill_dir / "SKILL.md"
    tests_dir = repo_root / "tests" / skill
    manifest_path = repo_root / "tests" / "skill-requirements.toml"
    manifest = load_manifest(manifest_path)
    problems: list[str] = []
    if "_error" in manifest:
        problems.append(f"cannot parse {manifest_path}: {manifest['_error']}")
        manifest = {}
    if not skill_md.is_file():
        problems.append(f"missing {skill_md.relative_to(repo_root)}")

    script_files = sorted(path for path in (skill_dir / "scripts").rglob("*") if path.is_file()) if (skill_dir / "scripts").is_dir() else []
    test_files = sorted(tests_dir.glob("test_*.py")) if tests_dir.is_dir() else []
    entry = (manifest.get("skills") or {}).get(skill)
    if script_files and not test_files:
        problems.append(f"script-bearing skill needs tests/{skill}/test_*.py")
    if script_files and entry is None:
        problems.append(f"script-bearing skill needs [skills.{skill}] in tests/skill-requirements.toml")

    commands: list[str] = [
        "uv sync --python 3.13",
        f"uv run skills-ref validate skills/{skill}",
    ]
    if changed_kind in {"new", "update", "shared"}:
        commands.append("uv run --with pytest python -m pytest tests/_meta -q")
    if test_files:
        commands.append(f"uv run --with pytest python -m pytest tests/{skill} -q")
    if entry is not None:
        commands.append(f"python tests/run_all.py --isolated {skill}")
    if changed_kind == "shared":
        commands.append("python tests/run_all.py")

    result = {
        "status": "fail" if problems else "pass",
        "repo_root": str(repo_root),
        "skill": skill,
        "changed_kind": changed_kind,
        "skill_dir_exists": skill_dir.is_dir(),
        "script_files": [str(path.relative_to(repo_root)) for path in script_files],
        "test_files": [str(path.relative_to(repo_root)) for path in test_files],
        "manifest_entry": entry,
        "problems": problems,
        "commands": commands,
    }
    return result, 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository checkout to inspect")
    parser.add_argument("--skill", required=True, help="Canonical skill directory name")
    parser.add_argument("--changed-kind", choices=("new", "update", "shared"), default="update")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a human-readable plan")
    args = parser.parse_args(argv)

    result, code = plan(Path(args.repo_root).resolve(), args.skill, args.changed_kind)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{result['status'].upper()}: {result.get('skill', args.skill)}")
        for problem in result.get("problems", []):
            print(f"- {problem}")
        print("\nRecommended commands:")
        for command in result.get("commands", []):
            print(f"  {command}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
