#!/usr/bin/env python3
"""Check a Muzic workspace for expected subprojects and common runtime assets.

This helper is intentionally lightweight: it does not import Muzic modules,
download models, run training, or mutate files. It validates directory layout
before a future agent chooses a sub-skill workflow.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

KNOWN_PROJECTS = {
    "musicbert": ["README.md", "preprocess.py"],
    "pdaugment": ["README.md", "pdaugment.py"],
    "clamp": ["README.md", "clamp.py"],
    "deeprapper": ["README.md", "generate.py"],
    "songmass": ["README.md", "infer_lyric.sh"],
    "telemelody": ["README.md", "inferrence/infer_en.py"],
    "relyme": ["Readme.md", "score"],
    "roc": ["README.md", "lyrics_to_melody.py"],
    "getmusic": ["README.md", "track_generation.py", "position_generation.py"],
    "musecoco": ["README.md", "1-text2attribute_model", "2-attribute2music_model"],
    "museformer": ["README.md", "museformer", "tools"],
    "meloform": ["README.md", "meloform_refine_melody.sh"],
    "emogen": ["readMe.md", "Piano_gen.sh"],
    "musicagent": ["README.md", "config.yaml", "agent.py"],
}

REQUIREMENT_FILES = [
    "requirements.txt",
    "clamp/requirements.txt",
    "musecoco/requirements.txt",
    "musicagent/requirements.txt",
]


def exists_report(base: Path, rels: Iterable[str]) -> list[dict[str, object]]:
    out = []
    for rel in rels:
        p = base / rel
        out.append({"path": rel, "exists": p.exists(), "kind": "dir" if p.is_dir() else "file" if p.is_file() else "missing"})
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Muzic workspace layout without running model code.")
    parser.add_argument("--workspace", default=".", help="Path to a Muzic checkout or workspace root.")
    parser.add_argument(
        "--expect",
        nargs="*",
        default=[],
        help="Optional subprojects expected by the user's task, e.g. musicbert clamp getmusic musicagent.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    result: dict[str, object] = {
        "workspace": str(workspace),
        "exists": workspace.exists(),
        "is_dir": workspace.is_dir(),
        "root_files": exists_report(workspace, ["README.md", "LICENSE"]),
        "requirements": exists_report(workspace, REQUIREMENT_FILES),
        "projects": {},
        "warnings": [],
        "errors": [],
    }

    if not workspace.is_dir():
        result["errors"].append("workspace is not a directory")
    else:
        projects: dict[str, object] = {}
        for project, markers in KNOWN_PROJECTS.items():
            base = workspace / project
            project_report = {
                "exists": base.is_dir(),
                "markers": exists_report(base, markers) if base.is_dir() else [],
            }
            projects[project] = project_report
        result["projects"] = projects

        expected = args.expect or []
        unknown = [p for p in expected if p not in KNOWN_PROJECTS]
        missing = [p for p in expected if p in KNOWN_PROJECTS and not (workspace / p).is_dir()]
        if unknown:
            result["warnings"].append(f"unknown project names in --expect: {', '.join(unknown)}")
        if missing:
            result["errors"].append(f"expected project directories missing: {', '.join(missing)}")
        if not (workspace / "README.md").is_file():
            result["warnings"].append("root README.md not found; this may not be a Muzic repository root")
        if (workspace / "musicagent" / ".env").exists():
            result["warnings"].append("musicagent/.env exists; do not print or commit secret values from it")

    exit_code = 1 if result["errors"] else 0
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Workspace: {workspace}")
        for item in result["root_files"]:  # type: ignore[index]
            print(f"root {item['path']}: {item['kind']}")
        print("\nRequirement files:")
        for item in result["requirements"]:  # type: ignore[index]
            print(f"  {item['path']}: {item['kind']}")
        print("\nProjects:")
        for project, info in sorted(result["projects"].items()):  # type: ignore[union-attr]
            status = "present" if info["exists"] else "missing"  # type: ignore[index]
            print(f"  {project}: {status}")
        for warning in result["warnings"]:  # type: ignore[index]
            print(f"WARNING: {warning}")
        for error in result["errors"]:  # type: ignore[index]
            print(f"ERROR: {error}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
