#!/usr/bin/env python3
"""Helpers for DeBERTa reduced recovery harnesses."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def authoritative_target(module_plan: dict) -> dict:
    target = dict(module_plan.get("fast_recovery_target", {}))
    if not target:
        raise ValueError("module_plan.fast_recovery_target is missing")
    return target


def reduced_recovery_allowed(run_manifest: dict, runtime_handoff: dict) -> bool:
    mode = run_manifest.get("recovery_mode", "hard")
    return bool(mode == "soft" and runtime_handoff.get("reduced_recovery_recommended") and runtime_handoff.get("blockers"))


def build_source_manifest(
    attempt_dir: str,
    generated_skills_root: str,
    paper_text_path: str,
    runtime_handoff_path: str,
) -> dict:
    sources = [
        "paper_text.txt",
        "paper_profile.md",
        "module_plan.json",
        "modules/",
        str(generated_skills_root),
        "environment/runtime_handoff.json",
        str(runtime_handoff_path),
    ]
    return {
        "schema_version": 1,
        "attempt_dir": str(attempt_dir),
        "allowed_sources_used": sources,
        "paper_text_path": paper_text_path,
        "runtime_handoff_path": runtime_handoff_path,
        "generated_skills_root": generated_skills_root,
        "forbidden_sources_detected": [],
        "original_repo_used": false_marker(),
        "benchmark_sources": {},
    }


def false_marker() -> bool:
    return False


def invocation(module: str, skill: str, evidence: str, artifact: str) -> dict:
    return {
        "module": module,
        "skill": skill,
        "evidence": evidence,
        "artifact": artifact,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module-plan", required=True)
    args = parser.parse_args()
    plan = load_json(args.module_plan)
    print(json.dumps(authoritative_target(plan), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
