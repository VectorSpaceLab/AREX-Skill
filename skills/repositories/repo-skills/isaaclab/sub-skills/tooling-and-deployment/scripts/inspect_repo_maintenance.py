#!/usr/bin/env python3
"""Print a safe maintainer checklist and repository version metadata."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_COMMANDS = {
    "format": "./isaaclab.sh -f",
    "docs": "./isaaclab.sh -d",
    "tests": "./isaaclab.sh -t",
    "python": "./isaaclab.sh -p",
}


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Isaac Lab maintenance metadata.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repository root to inspect.")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    version = _read_text(repo_root / "VERSION")
    pyproject = _read_text(repo_root / "pyproject.toml")
    has_skills = (repo_root / "skills").exists()

    report = {
        "repo_root": repo_root.name,
        "version": version,
        "has_skills_tree": has_skills,
        "maintenance_commands": DEFAULT_COMMANDS,
        "present_metadata": {
            "VERSION": version is not None,
            "pyproject.toml": pyproject is not None,
        },
        "changelog_policy": "Use fragments under source/<pkg>/changelog.d/ instead of editing compiled changelogs.",
    }

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Version: {version or '(missing)'}")
        print(f"Skills tree present: {has_skills}")
        for name, command in DEFAULT_COMMANDS.items():
            print(f"{name}: {command}")
        print(report["changelog_policy"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
