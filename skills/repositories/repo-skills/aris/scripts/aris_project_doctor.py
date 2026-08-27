#!/usr/bin/env python3
"""Read-only ARIS project doctor.

Checks a target research project for ARIS installation indicators, manifests,
skill directories, helper links, research-wiki state, and optional host tools.
It does not run installers, mutate files, call external APIs, or start MCP
servers.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any

HOST_LAYOUTS = {
    "claude": {"skill_root": ".claude/skills", "manifest": ".aris/installed-skills.txt"},
    "codex": {"skill_root": ".agents/skills", "manifest": ".aris/installed-skills-codex.txt"},
    "copilot": {"skill_root": ".github/skills", "manifest": ".aris/installed-skills-copilot.txt"},
}

OPTIONAL_COMMANDS = ["claude", "codex", "gemini", "latexmk", "pdfinfo", "git", "screen", "tmux", "nvidia-smi"]


def parse_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "entries": [], "repo_root": None, "raw_lines": 0}
    entries: list[str] = []
    repo_root = None
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines:
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if parts[0] == "repo_root" and len(parts) >= 2:
            repo_root = parts[1]
        elif parts[0] in {"skill", "entry"} and len(parts) >= 2:
            entries.append(parts[1])
        elif len(parts) == 1 and parts[0]:
            # Older/simple manifests sometimes store one skill name per line.
            entries.append(parts[0])
    return {"exists": True, "entries": sorted(set(entries)), "repo_root": repo_root, "raw_lines": len(lines)}


def inspect_skill_root(project: Path, rel: str) -> dict[str, Any]:
    root = project / rel
    if not root.exists():
        return {"exists": False, "count": 0, "sample": [], "symlink_count": 0, "real_dir_count": 0}
    children = [p for p in root.iterdir() if p.name not in {".", ".."}]
    skills = [p for p in children if (p / "SKILL.md").exists() or p.is_symlink()]
    return {
        "exists": True,
        "count": len(skills),
        "sample": sorted(p.name for p in skills)[:20],
        "symlink_count": sum(1 for p in skills if p.is_symlink()),
        "real_dir_count": sum(1 for p in skills if p.is_dir() and not p.is_symlink()),
    }


def inspect_research_wiki(project: Path) -> dict[str, Any]:
    root = project / "research-wiki"
    expected = ["index.md", "log.md", "gap_map.md", "query_pack.md", "graph/edges.jsonl"]
    return {
        "exists": root.exists(),
        "files": {name: (root / name).exists() for name in expected},
        "paper_count": len(list((root / "papers").glob("*.md"))) if (root / "papers").exists() else 0,
        "idea_count": len(list((root / "ideas").glob("*.md"))) if (root / "ideas").exists() else 0,
        "experiment_count": len(list((root / "experiments").glob("*.md"))) if (root / "experiments").exists() else 0,
    }


def inspect_project(project: Path) -> dict[str, Any]:
    project = project.expanduser().resolve()
    result: dict[str, Any] = {
        "project": str(project),
        "exists": project.exists(),
        "host_tools": {cmd: shutil.which(cmd) is not None for cmd in OPTIONAL_COMMANDS},
        "hosts": {},
        "aris_tools": {},
        "research_wiki": {},
        "state_files": {},
        "warnings": [],
    }
    if not project.exists():
        result["warnings"].append("project path does not exist")
        return result

    for host, layout in HOST_LAYOUTS.items():
        manifest = project / layout["manifest"]
        result["hosts"][host] = {
            "skill_root": inspect_skill_root(project, layout["skill_root"]),
            "manifest": parse_manifest(manifest),
        }

    aris_tools = project / ".aris" / "tools"
    result["aris_tools"] = {
        "exists": aris_tools.exists(),
        "is_symlink": aris_tools.is_symlink(),
        "has_research_wiki_helper": (aris_tools / "research_wiki.py").exists(),
        "has_watchdog_helper": (aris_tools / "watchdog.py").exists(),
    }
    result["research_wiki"] = inspect_research_wiki(project)
    for name in ["CLAUDE.md", "AGENTS.md", "PIPELINE_STATUS.md", "EXPERIMENT_PLAN.md", "EXPERIMENT_LOG.md", "NARRATIVE_REPORT.md", "REVIEW_STATE.json"]:
        result["state_files"][name] = (project / name).exists()

    if not any(result["hosts"][h]["skill_root"]["exists"] for h in HOST_LAYOUTS):
        result["warnings"].append("no ARIS host skill root found")
    if not result["aris_tools"]["exists"]:
        result["warnings"].append(".aris/tools helper path is missing")
    if result["research_wiki"]["exists"] and not result["research_wiki"]["files"].get("query_pack.md"):
        result["warnings"].append("research-wiki exists but query_pack.md is missing")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only ARIS project doctor")
    parser.add_argument("--project", default=".", help="target research project directory")
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    args = parser.parse_args()

    report = inspect_project(Path(args.project))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    print(f"ARIS project doctor: {report['project']}")
    print(f"exists: {report['exists']}")
    print("\nHost skill roots:")
    for host, info in report["hosts"].items():
        sr = info["skill_root"]
        mf = info["manifest"]
        print(f"- {host}: skills={sr['count']} root_exists={sr['exists']} manifest={mf['exists']} entries={len(mf['entries'])}")
    print("\nHelper path:")
    print(f"- .aris/tools exists={report['aris_tools'].get('exists')} symlink={report['aris_tools'].get('is_symlink')}")
    print("\nResearch wiki:")
    rw = report["research_wiki"]
    print(f"- exists={rw.get('exists')} papers={rw.get('paper_count')} ideas={rw.get('idea_count')} experiments={rw.get('experiment_count')}")
    print("\nOptional host commands:")
    for cmd, ok in report["host_tools"].items():
        print(f"- {cmd}: {'found' if ok else 'missing'}")
    if report["warnings"]:
        print("\nWarnings:")
        for warning in report["warnings"]:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
