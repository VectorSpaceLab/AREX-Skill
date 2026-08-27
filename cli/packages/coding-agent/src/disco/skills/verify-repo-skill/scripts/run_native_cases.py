#!/usr/bin/env python3
"""Run preselected native repo verification cases with timeouts.

This helper intentionally does not discover tests or decide what is safe.
The agent must provide a manifest containing only commands it has classified
as safe to run for the current environment.

Example:
  python run_native_cases.py \
    --repo-root /path/to/repo \
    --manifest reports/verification/native-ground-truth-candidates.json \
    --out reports/verification/native-verification-report.json \
    --timeout 120
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


RUNNABLE_SAFETY = {"safe-runnable", "help-only", "tiny-fixture-runnable"}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("manifest must be a JSON object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalize_cases(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    cases = manifest.get("cases")
    if cases is None:
        cases = manifest.get("native_cases")
    if not isinstance(cases, list):
        raise ValueError("manifest must contain a 'cases' list")
    normalized = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"case {index} must be an object")
        normalized.append(case)
    return normalized


def render_command(command: str, repo_root: Path, python_executable: str) -> str:
    return command.replace("$REPO_ROOT", str(repo_root)).replace("$PYTHON", python_executable)


def run_case(case: dict[str, Any], repo_root: Path, default_timeout: int, python_executable: str) -> dict[str, Any]:
    case_id = str(case.get("id") or case.get("name") or "unnamed")
    safety = str(case.get("safety_class") or case.get("safety") or "skip-unknown")
    backend_requirement = str(case.get("backend_requirement") or "any").strip().lower()
    backend_criticality = str(case.get("backend_criticality") or "optional").strip().lower()
    cpu_substitute = str(case.get("cpu_substitute") or "partial").strip().lower()
    command = case.get("command")
    expected_skill_area = case.get("expected_skill_area") or case.get("skill_area")
    evidence_path = case.get("evidence_path") or case.get("artifact")
    timeout = int(case.get("timeout_seconds") or default_timeout)
    blocked_required_backend = (
        backend_criticality == "required"
        and cpu_substitute != "full"
        and backend_requirement not in {"", "any", "cpu"}
    )

    result: dict[str, Any] = {
        "id": case_id,
        "workflow": case.get("workflow") or case.get("capability"),
        "evidence_path": evidence_path,
        "expected_skill_area": expected_skill_area,
        "safety_class": safety,
        "backend_requirement": backend_requirement,
        "backend_criticality": backend_criticality,
        "cpu_substitute": cpu_substitute,
        "dependency_variant": case.get("dependency_variant"),
        "hardware_prerequisites": case.get("hardware_prerequisites"),
        "verification_expectation": case.get("verification_expectation"),
        "assigned_environment": case.get("assigned_environment"),
        "command": command,
    }

    if safety not in RUNNABLE_SAFETY:
        result.update(
            {
                "status": "BLOCKED_REQUIRED_BACKEND" if blocked_required_backend else "SKIP_UNSAFE",
                "reason": case.get("skip_reason") or f"safety_class is {safety}",
            }
        )
        return result

    if not isinstance(command, str) or not command.strip():
        result.update(
            {
                "status": "BLOCKED_REQUIRED_BACKEND" if blocked_required_backend else "SKIP_UNSAFE",
                "reason": "missing command",
            }
        )
        return result

    rendered = render_command(command, repo_root, python_executable)
    started = time.monotonic()
    try:
        completed = subprocess.run(
            rendered,
            cwd=repo_root,
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        elapsed = time.monotonic() - started
        result.update(
            {
                "rendered_command": rendered,
                "exit_code": completed.returncode,
                "elapsed_seconds": round(elapsed, 3),
                "stdout_tail": completed.stdout[-4000:],
                "stderr_tail": completed.stderr[-4000:],
                "status": "PASS" if completed.returncode == 0 else "NATIVE_FAIL",
            }
        )
    except subprocess.TimeoutExpired as exc:
        result.update(
            {
                "rendered_command": rendered,
                "elapsed_seconds": timeout,
                "stdout_tail": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
                "stderr_tail": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
                "status": "NATIVE_FAIL",
                "reason": f"timeout after {timeout} seconds",
            }
        )
    return result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="Repository root used as cwd for native commands.")
    parser.add_argument("--manifest", required=True, help="JSON manifest of preselected native cases.")
    parser.add_argument("--out", required=True, help="JSON report output path.")
    parser.add_argument("--timeout", type=int, default=120, help="Default per-case timeout in seconds.")
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable substituted for $PYTHON in manifest commands.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).expanduser().resolve()
    manifest_path = Path(args.manifest).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()

    manifest = load_json(manifest_path)
    cases = normalize_cases(manifest)

    report: dict[str, Any] = {
        "schema": "disco.native-verification-report.v2",
        "repo_root_basename": repo_root.name,
        "manifest": str(manifest_path),
        "case_count": len(cases),
        "results": [],
        "summary": {},
    }

    for case in cases:
        report["results"].append(run_case(case, repo_root, args.timeout, args.python))

    summary: dict[str, int] = {}
    for result in report["results"]:
        status = str(result.get("status") or "UNKNOWN")
        summary[status] = summary.get(status, 0) + 1
    report["summary"] = summary

    write_json(out_path, report)
    print(json.dumps(report["summary"], sort_keys=True))

    if summary.get("NATIVE_FAIL", 0) > 0 or summary.get("BLOCKED_REQUIRED_BACKEND", 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
