#!/usr/bin/env python3
"""Plan a repository security scan without running networked analysis.

The helper checks target directories and reports whether the scanner key is
present as a boolean. It never prints the key and never starts a scanner.

Examples:
    python plan_security_scan.py --repo-root . --mode changed --skill scanpy --fail-on HIGH
    python plan_security_scan.py --repo-root . --mode full --workers 4 --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "NEVER")


def build_plan(
    repo_root: Path,
    mode: str,
    skills: list[str],
    fail_on: str,
    output: str,
    workers: int,
) -> tuple[dict, int]:
    if not repo_root.is_dir():
        return {"status": "error", "problems": [f"repo root does not exist: {repo_root}"]}, 2
    problems: list[str] = []
    targets: list[str] = []
    if mode == "changed":
        if not skills:
            problems.append("changed mode needs at least one --skill")
        for skill in skills:
            if not skill or "/" in skill or "\\" in skill:
                problems.append(f"invalid skill name: {skill!r}")
                continue
            skill_dir = repo_root / "skills" / skill
            if not (skill_dir / "SKILL.md").is_file():
                problems.append(f"missing skills/{skill}/SKILL.md")
            else:
                targets.append(f"skills/{skill}")
    key_present = bool(os.getenv("SKILL_SCANNER_LLM_API_KEY"))
    if mode == "changed":
        command = [
            "uv run python scan_pr_skills.py",
            f"--output {output}",
            f"--fail-on {fail_on}",
            *targets,
        ]
    else:
        command = [
            "uv run python scan_skills.py",
            f"--workers {workers}",
            *(["--full"] if output == "FULL" else []),
        ]
    result = {
        "status": "fail" if problems else "pass",
        "repo_root": str(repo_root),
        "mode": mode,
        "skills": skills,
        "targets": targets,
        "fail_on": fail_on,
        "output": output,
        "workers": workers,
        "llm_api_key_present": key_present,
        "network_scan_authorized": False,
        "command": " ".join(command),
        "warnings": [
            "The helper does not run the command.",
            "LLM-backed scans need explicit network/API-key approval.",
            "Unset SKILL_SCANNER_LLM_API_KEY makes scan_pr_skills.py write an explanatory no-op comment and exit 0.",
        ],
        "problems": problems,
    }
    return result, 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository checkout to inspect")
    parser.add_argument("--mode", choices=("changed", "full"), default="changed")
    parser.add_argument("--skill", action="append", default=[], help="Skill name; repeat for multiple changed skills")
    parser.add_argument("--fail-on", choices=SEVERITIES, default="HIGH")
    parser.add_argument("--output", default="pr_scan_comment.md", help="PR comment path for changed mode; use FULL for --full")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.workers < 1:
        parser.error("--workers must be at least 1")
    result, code = build_plan(
        Path(args.repo_root).resolve(),
        args.mode,
        args.skill,
        args.fail_on,
        args.output,
        args.workers,
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{result['status'].upper()}: {result['mode']} security scan plan")
        print(f"LLM key present: {'yes' if result.get('llm_api_key_present') else 'no'}")
        for warning in result.get("warnings", []):
            print(f"- {warning}")
        for problem in result.get("problems", []):
            print(f"- {problem}")
        print(f"Command: {result.get('command', '')}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
