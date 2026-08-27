#!/usr/bin/env python3
"""Inspect a DeepResearch checkout for expected operating-skill evidence.

This stdlib-only helper is safe to run before trusting exact DeepResearch command
or field guidance. It checks relative files, Git state when available, large
asset blockers, and selected script interfaces without importing the source
checkout or contacting services.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

EXPECTED_COMMIT = "f72f75d8c3eb842f2bbbab096a12206ff66e270f"

REQUIRED_FILES = [
    "README.md",
    "FAQ.md",
    ".env.example",
    "requirements.txt",
    "inference/run_react_infer.sh",
    "inference/run_multi_react.py",
    "inference/react_agent.py",
    "inference/prompt.py",
    "inference/tool_search.py",
    "inference/tool_visit.py",
    "inference/tool_scholar.py",
    "inference/tool_python.py",
    "inference/tool_file.py",
    "inference/eval_data/example.jsonl",
    "inference/eval_data/example_with_file.jsonl",
    "evaluation/evaluate_deepsearch_official.py",
    "evaluation/evaluate_hle_official.py",
    "WebAgent/README.md",
]

FAMILY_DOCS = [
    "WebAgent/WebDancer/readme.md",
    "WebAgent/WebSailor/README.md",
    "WebAgent/WebSailor-V2/README.md",
    "WebAgent/WebShaper/readme.md",
    "WebAgent/WebWatcher/README.md",
    "WebAgent/WebResearcher/README.md",
    "WebAgent/WebResummer/README.md",
    "WebAgent/WebWeaver/README.md",
    "WebAgent/WebWalker/README.md",
    "WebAgent/WebLeaper/README.md",
    "Agent/AgentFounder/README.md",
    "Agent/AgentScaler/README.md",
]

LARGE_OR_BLOCKED_HINTS = [
    "WebAgent/WebWatcher/browsecomp-vl/images/level1.tar",
    "WebAgent/WebWatcher/browsecomp-vl/images/level2.tar",
    "WebAgent/WebWatcher/infer/scripts_eval/images/hle_imgs.tar",
    "WebAgent/WebWatcher/infer/vl_search_r1/qwen-agent-o1_search",
    "WebAgent/WebWeaver/tool/redis_for_sdk-0.1.0-py3-none-any.whl",
]

TEXT_PROBES = {
    "inference/run_react_infer.sh": ["vllm serve", "6001", "6008", "run_multi_react.py"],
    "inference/run_multi_react.py": ["--dataset", "--output", "--roll_out_count", "iter1.jsonl"],
    "evaluation/evaluate_deepsearch_official.py": ["--input_folder", "--dataset", "pass_at_3"],
    "evaluation/evaluate_hle_official.py": ["--input_fp", "--tokenizer_path", "openai/o3-mini"],
}


def run_git(repo: Path, args: Sequence[str]) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, timeout=10)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as exc:  # pragma: no cover - platform dependent
        return 127, "", str(exc)


def rel_exists(repo: Path, rel: str) -> bool:
    return (repo / rel).exists()


def file_size(repo: Path, rel: str) -> int | None:
    path = repo / rel
    if not path.exists() or not path.is_file():
        return None
    return path.stat().st_size


def check_text_probes(repo: Path) -> Dict[str, Dict[str, object]]:
    out: Dict[str, Dict[str, object]] = {}
    for rel, needles in TEXT_PROBES.items():
        path = repo / rel
        if not path.exists() or not path.is_file():
            out[rel] = {"exists": False, "missing_needles": needles}
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            out[rel] = {"exists": True, "error": str(exc), "missing_needles": needles}
            continue
        missing = [needle for needle in needles if needle not in text]
        out[rel] = {"exists": True, "missing_needles": missing}
    return out


def summarize_tree(repo: Path) -> Dict[str, object]:
    required_missing = [rel for rel in REQUIRED_FILES if not rel_exists(repo, rel)]
    family_present = [rel for rel in FAMILY_DOCS if rel_exists(repo, rel)]
    family_missing = [rel for rel in FAMILY_DOCS if not rel_exists(repo, rel)]
    blocker_hints = []
    for rel in LARGE_OR_BLOCKED_HINTS:
        path = repo / rel
        if path.exists():
            item = {"path": rel, "type": "dir" if path.is_dir() else "file"}
            size = file_size(repo, rel)
            if size is not None:
                item["size_bytes"] = size
            blocker_hints.append(item)
    return {
        "required_missing": required_missing,
        "family_docs_present": family_present,
        "family_docs_missing": family_missing,
        "large_or_blocked_hints": blocker_hints,
        "text_probes": check_text_probes(repo),
    }


def git_snapshot(repo: Path) -> Dict[str, object]:
    if not (repo / ".git").exists():
        return {"vcs": "none"}
    rc_head, head, err_head = run_git(repo, ["rev-parse", "HEAD"])
    rc_branch, branch, _ = run_git(repo, ["branch", "--show-current"])
    rc_status, status, _ = run_git(repo, ["status", "--short"])
    rc_remote, remote, _ = run_git(repo, ["remote", "get-url", "origin"])
    return {
        "vcs": "git",
        "commit": head if rc_head == 0 else None,
        "commit_error": err_head if rc_head != 0 else None,
        "expected_skill_commit": EXPECTED_COMMIT,
        "commit_matches_skill": head == EXPECTED_COMMIT if rc_head == 0 else False,
        "branch": branch if rc_branch == 0 else None,
        "remote_url": remote if rc_remote == 0 else None,
        "dirty_paths": status.splitlines() if status else [],
    }


def render_text(report: Dict[str, object]) -> str:
    lines = ["# DeepResearch Checkout Inspection", ""]
    git = report["git"]
    if git.get("vcs") == "git":
        lines.append(f"Commit: {git.get('commit')} (matches skill: {git.get('commit_matches_skill')})")
        lines.append(f"Branch: {git.get('branch') or 'unknown'}")
        dirty = git.get("dirty_paths") or []
        lines.append(f"Dirty paths: {len(dirty)}")
    else:
        lines.append("Git: not a Git checkout")
    tree = report["tree"]
    missing = tree["required_missing"]
    lines.append("")
    lines.append(f"Required evidence missing: {len(missing)}")
    for rel in missing:
        lines.append(f"  - {rel}")
    lines.append(f"Family docs present: {len(tree['family_docs_present'])}/{len(FAMILY_DOCS)}")
    if tree["large_or_blocked_hints"]:
        lines.append("Large or blocked-workflow hints present:")
        for item in tree["large_or_blocked_hints"]:
            suffix = f" ({item.get('size_bytes')} bytes)" if "size_bytes" in item else ""
            lines.append(f"  - {item['path']} [{item['type']}]{suffix}")
    probe_failures = []
    for rel, info in tree["text_probes"].items():
        if info.get("missing_needles"):
            probe_failures.append((rel, info["missing_needles"]))
    if probe_failures:
        lines.append("Script interface probes with missing markers:")
        for rel, needles in probe_failures:
            lines.append(f"  - {rel}: missing {', '.join(needles)}")
    if not missing and not probe_failures:
        lines.append("Core evidence and script interface markers look compatible with this skill.")
    if git.get("vcs") == "git" and not git.get("commit_matches_skill"):
        lines.append("WARNING: checkout commit differs from this skill provenance; refresh may be needed for exact commands.")
    return "\n".join(lines)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect a DeepResearch checkout for compatibility with this generated repo skill.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="DeepResearch checkout to inspect")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo = args.repo_root.expanduser().resolve()
    report = {"repo_root_name": repo.name, "git": git_snapshot(repo), "tree": summarize_tree(repo)}
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_text(report))
    missing = report["tree"]["required_missing"]
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
