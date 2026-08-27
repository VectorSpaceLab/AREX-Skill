#!/usr/bin/env python3
"""Smoke-check the llm-rl-visualized runtime skill tree.

This script validates that the generated skill tree is internally consistent,
its bundled JSON files parse, and its helper scripts respond to safe checks.
It does not require the original source checkout beyond the skill tree itself.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-check the llm-rl-visualized skill tree.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Path to the generated llm-rl-visualized skill root. Defaults to the script's parent skill tree.",
    )
    return parser.parse_args()


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path, root: Path, problems: list[str]) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        problems.append(f"invalid JSON in {rel(path, root)}: {exc}")
        return None


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def require(path: Path, root: Path, problems: list[str]) -> None:
    if not path.exists():
        problems.append(f"missing required file: {rel(path, root)}")


def check_contains(label: str, proc: subprocess.CompletedProcess[str], needles: list[str], problems: list[str]) -> None:
    if proc.returncode != 0:
        problems.append(f"{label} failed with exit code {proc.returncode}: {proc.stderr.strip() or proc.stdout.strip()}")
        return
    text = proc.stdout + "\n" + proc.stderr
    for needle in needles:
        if needle not in text:
            problems.append(f"{label} did not contain expected text: {needle!r}")


def main() -> int:
    args = parse_args()
    root = args.root.expanduser().resolve()
    problems: list[str] = []

    required_files = [
        root / "SKILL.md",
        root / "references" / "repo-overview.md",
        root / "references" / "repo-provenance.md",
        root / "references" / "repo-routing-metadata.json",
        root / "references" / "troubleshooting.md",
        root / "sub-skills" / "knowledge-atlas" / "SKILL.md",
        root / "sub-skills" / "knowledge-atlas" / "references" / "atlas-guide.md",
        root / "sub-skills" / "knowledge-atlas" / "references" / "atlas-index.json",
        root / "sub-skills" / "knowledge-atlas" / "references" / "model-catalog-guide.md",
        root / "sub-skills" / "knowledge-atlas" / "references" / "book-code-snippets.md",
        root / "sub-skills" / "knowledge-atlas" / "references" / "citation-and-license.md",
        root / "sub-skills" / "knowledge-atlas" / "references" / "troubleshooting.md",
        root / "sub-skills" / "knowledge-atlas" / "scripts" / "search_atlas.py",
        root / "sub-skills" / "asset-maintenance" / "SKILL.md",
        root / "sub-skills" / "asset-maintenance" / "references" / "asset-layout.md",
        root / "sub-skills" / "asset-maintenance" / "references" / "maintenance-workflows.md",
        root / "sub-skills" / "asset-maintenance" / "references" / "troubleshooting.md",
        root / "sub-skills" / "asset-maintenance" / "scripts" / "asset_maintenance.py",
    ]
    for path in required_files:
        require(path, root, problems)

    atlas_index = load_json(root / "sub-skills" / "knowledge-atlas" / "references" / "atlas-index.json", root, problems)
    routing = load_json(root / "references" / "repo-routing-metadata.json", root, problems)

    if atlas_index is not None:
        entries = atlas_index.get("entries")
        if not isinstance(entries, list) or not entries:
            problems.append("atlas-index.json does not contain a non-empty 'entries' list")
        else:
            ids = {entry.get("id") for entry in entries if isinstance(entry, dict)}
            for required_id in {"llm-basics", "sft-lora", "dpo", "policy-optimization", "rlhf-rlaif", "model-catalog"}:
                if required_id not in ids:
                    problems.append(f"atlas-index.json missing expected entry id: {required_id}")

    if routing is not None:
        if "skills" not in routing or "scenarios" not in routing:
            problems.append("repo-routing-metadata.json must contain top-level 'skills' and 'scenarios'")
        else:
            skill = routing.get("skills", {}).get("llm-rl-visualized")
            if not skill:
                problems.append("repo-routing-metadata.json missing llm-rl-visualized skill routing")
            else:
                scenario_ids = {entry.get("id") for entry in skill.get("scenarios", []) if isinstance(entry, dict)}
                for required_id in {"llm-rl-visual-atlas", "python-repository-maintenance"}:
                    if required_id not in scenario_ids:
                        problems.append(f"repo-routing-metadata.json missing scenario id for skill: {required_id}")

    search_script = root / "sub-skills" / "knowledge-atlas" / "scripts" / "search_atlas.py"
    asset_script = root / "sub-skills" / "asset-maintenance" / "scripts" / "asset_maintenance.py"

    if search_script.exists():
        ppo = run([sys.executable, str(search_script), "--query", "PPO"], cwd=root)
        check_contains("search_atlas.py --query PPO", ppo, ["policy-optimization", "PPO"], problems)
        rope = run([sys.executable, str(search_script), "--query", "RoPE"], cwd=root)
        check_contains("search_atlas.py --query RoPE", rope, ["llm-extensions", "RoPE"], problems)

    if asset_script.exists():
        help_proc = run([sys.executable, str(asset_script), "--help"], cwd=root)
        check_contains("asset_maintenance.py --help", help_proc, ["inventory", "rename-plan", "add-name-column", "trim"], problems)

    if problems:
        for problem in problems:
            print(f"error: {problem}", file=sys.stderr)
        return 1

    print(f"ok: smoke check passed for {root.name}")
    print("- JSON files parsed")
    print("- route metadata present")
    print("- search helper returned PPO and RoPE matches")
    print("- asset helper responded to --help")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
