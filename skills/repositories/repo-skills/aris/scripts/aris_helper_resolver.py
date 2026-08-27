#!/usr/bin/env python3
"""Resolve ARIS helper scripts without executing them.

This mirrors the documented ARIS helper lookup idea in a strict, read-only
form: project-local helpers first, then an ARIS repo pointer from environment,
manifest, or the user's global pointer file. It prints the selected path and
why it was chosen, or exits with status 42 when no helper can be found.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def manifest_repo_root(project: Path) -> str | None:
    for name in ["installed-skills.txt", "installed-skills-codex.txt", "installed-skills-copilot.txt"]:
        path = project / ".aris" / name
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and parts[0] == "repo_root" and parts[1].strip():
                return parts[1].strip()
    return None


def global_pointer(home: Path) -> str | None:
    path = home / ".aris" / "repo"
    if not path.exists():
        return None
    value = path.read_text(encoding="utf-8", errors="replace").strip()
    return value or None


def resolve_helper(project: Path, helper: str, aris_repo: str | None = None, skill_dir: Path | None = None, home: Path | None = None) -> dict[str, Any]:
    project = project.expanduser().resolve()
    home = (home or Path.home()).expanduser()
    tried: list[dict[str, str]] = []

    def check(label: str, path: Path) -> dict[str, Any] | None:
        tried.append({"layer": label, "path": str(path)})
        if path.is_file():
            return {"found": True, "layer": label, "path": str(path), "tried": tried}
        return None

    if skill_dir is not None:
        result = check("skill-owned", skill_dir.expanduser().resolve() / "scripts" / helper)
        if result:
            return result

    for label, path in [
        ("project-.aris-tools", project / ".aris" / "tools" / helper),
        ("project-tools", project / "tools" / helper),
    ]:
        result = check(label, path)
        if result:
            return result

    repo_candidates: list[tuple[str, str | None]] = [
        ("env-ARIS_REPO", aris_repo or os.environ.get("ARIS_REPO")),
        ("manifest-repo_root", manifest_repo_root(project)),
        ("home-pointer", global_pointer(home)),
    ]
    for label, repo in repo_candidates:
        if not repo:
            tried.append({"layer": label, "path": "<unset>"})
            continue
        result = check(label, Path(repo).expanduser() / "tools" / helper)
        if result:
            return result
    return {"found": False, "path": None, "tried": tried}


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve an ARIS helper path without executing it")
    parser.add_argument("--project", default=".", help="target research project")
    parser.add_argument("--helper", required=True, help="helper filename such as research_wiki.py")
    parser.add_argument("--aris-repo", default=None, help="explicit ARIS repo root override")
    parser.add_argument("--skill-dir", default=None, help="optional current skill directory for skill-owned helpers")
    parser.add_argument("--home", default=None, help="override home directory for testing")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    report = resolve_helper(
        project=Path(args.project),
        helper=args.helper,
        aris_repo=args.aris_repo,
        skill_dir=Path(args.skill_dir) if args.skill_dir else None,
        home=Path(args.home) if args.home else None,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif report.get("found"):
        print(report["path"])
        print(f"layer: {report['layer']}")
    else:
        print(f"helper not found: {args.helper}")
        for item in report["tried"]:
            print(f"- {item['layer']}: {item['path']}")
    return 0 if report.get("found") else 42


if __name__ == "__main__":
    raise SystemExit(main())
