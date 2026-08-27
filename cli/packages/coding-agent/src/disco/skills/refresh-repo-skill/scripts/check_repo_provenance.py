#!/usr/bin/env python3
"""Compare a repo skill provenance snapshot with the current Git checkout."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_git(repo: Path, args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.returncode, proc.stdout.rstrip("\n"), proc.stderr.strip()


def extract_json_block(markdown: str) -> dict[str, Any]:
    match = re.search(r"```json\s*(\{.*?\})\s*```", markdown, re.DOTALL)
    if not match:
        raise ValueError("No fenced JSON block found in repo-provenance.md")
    data = json.loads(match.group(1))
    if not isinstance(data, dict):
        raise ValueError("Provenance JSON must be an object")
    return data


def read_provenance(skill_dir: Path) -> tuple[Path, dict[str, Any] | None, str | None]:
    provenance_path = skill_dir / "references" / "repo-provenance.md"
    if not provenance_path.exists():
        return provenance_path, None, "missing_provenance"
    try:
        return provenance_path, extract_json_block(provenance_path.read_text(encoding="utf-8")), None
    except Exception as exc:  # noqa: BLE001 - report parse failures to the agent.
        return provenance_path, None, f"invalid_provenance: {exc}"


def parse_dirty_paths(status: str) -> list[str]:
    paths: list[str] = []
    for line in status.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip() if len(line) > 3 else line.strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        paths.append(path)
    return sorted(paths)


def path_exists(repo: Path, rel_path: str) -> bool:
    if not rel_path or rel_path.startswith("/") or ".." in Path(rel_path).parts:
        return False
    return (repo / rel_path).exists()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-dir", required=True, help="Existing skill directory containing SKILL.md.")
    parser.add_argument("--repo-path", required=True, help="Current repository checkout path.")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    repo = Path(args.repo_path).resolve()
    provenance_path, provenance, provenance_error = read_provenance(skill_dir)

    result: dict[str, Any] = {
        "schema": "disco.repo-provenance-check.v1",
        "skill_dir": str(skill_dir),
        "repo_path": str(repo),
        "provenance_path": str(provenance_path),
        "status": "unknown",
        "checks": {},
        "warnings": [],
    }

    if provenance_error:
        result["status"] = "unknown"
        result["warnings"].append(provenance_error)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2

    if provenance is None:
        result["status"] = "unknown"
        result["warnings"].append("missing_provenance")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2

    repo_info = provenance.get("repository") if isinstance(provenance.get("repository"), dict) else {}
    evidence = provenance.get("evidence") if isinstance(provenance.get("evidence"), dict) else {}

    code, current_commit, err = run_git(repo, ["rev-parse", "HEAD"])
    if code == 0:
        expected_commit = repo_info.get("commit")
        result["checks"]["commit"] = {
            "expected": expected_commit,
            "current": current_commit,
            "matches": bool(expected_commit) and expected_commit == current_commit,
        }
    else:
        result["warnings"].append(f"git_rev_parse_failed: {err}")

    code, current_branch, _err = run_git(repo, ["branch", "--show-current"])
    if code == 0:
        expected_branch = repo_info.get("branch")
        result["checks"]["branch"] = {
            "expected": expected_branch,
            "current": current_branch or None,
            "matches": not expected_branch or expected_branch == current_branch,
        }

    code, status_text, err = run_git(repo, ["status", "--short"])
    if code == 0:
        current_dirty_paths = parse_dirty_paths(status_text)
        current_working_tree = "dirty" if current_dirty_paths else "clean"
        expected_dirty_paths = sorted(repo_info.get("dirty_paths") or [])
        expected_working_tree = repo_info.get("working_tree")
        result["checks"]["working_tree"] = {
            "expected": expected_working_tree,
            "current": current_working_tree,
            "matches": expected_working_tree == current_working_tree,
        }
        result["checks"]["dirty_paths"] = {
            "expected": expected_dirty_paths,
            "current": current_dirty_paths,
            "matches": expected_dirty_paths == current_dirty_paths,
        }
    else:
        result["warnings"].append(f"git_status_failed: {err}")

    evidence_checks: dict[str, Any] = {}
    for category, paths in evidence.items():
        if not isinstance(paths, list):
            continue
        evidence_checks[category] = [
            {"path": rel_path, "exists": path_exists(repo, rel_path)}
            for rel_path in paths
            if isinstance(rel_path, str)
        ]
    result["checks"]["evidence_paths"] = evidence_checks

    hard_mismatches = []
    for key in ("commit", "working_tree", "dirty_paths"):
        check = result["checks"].get(key)
        if isinstance(check, dict) and check.get("matches") is False:
            hard_mismatches.append(key)

    missing_evidence = [
        item["path"]
        for items in evidence_checks.values()
        for item in items
        if isinstance(item, dict) and item.get("exists") is False
    ]
    if missing_evidence:
        hard_mismatches.append("evidence_paths")
        result["warnings"].append(f"missing_evidence_paths: {', '.join(missing_evidence)}")

    result["status"] = "stale" if hard_mismatches else "current"
    result["mismatches"] = hard_mismatches
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if hard_mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
