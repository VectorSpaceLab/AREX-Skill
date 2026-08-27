#!/usr/bin/env python3
"""Report key PyOD repository maintenance surfaces without mutating files.

The checker is intentionally read-only. It inspects a PyOD checkout for expected
source/docs/scripts/tests, parses package metadata when possible, reports command
availability, and optionally runs small import/CLI probes with the selected
Python interpreter.

Examples:
    python repo_surface_check.py --repo-root /path/to/pyod
    python repo_surface_check.py --repo-root . --format json
    python repo_surface_check.py --repo-root . --import-check --strict
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - fallback for older users
    tomllib = None  # type: ignore[assignment]


CORE_FILES = [
    "pyproject.toml",
    "requirements.txt",
    "pyod/__init__.py",
    "pyod/version.py",
    "pyod/cli.py",
    "pyod/mcp_server.py",
    "pyod/models/base.py",
    "pyod/utils/ad_engine.py",
    "pyod/skills/__init__.py",
    "pyod/skills/od_expert/SKILL.md",
    "pyod/skills/od_expert/references/workflow.md",
    "docs/skill_maintenance.rst",
    "docs/examples/agentic.rst",
    "scripts/regen_skill.py",
    "scripts/render_agentic_demo.py",
]

RELEVANT_TESTS = [
    "pyod/test/test_cli.py",
    "pyod/test/test_mcp_server_import.py",
    "pyod/test/test_regen_skill.py",
    "pyod/test/test_skill_kb_consistency.py",
    "pyod/test/test_skill_api_refs.py",
    "pyod/test/test_persistence.py",
    "pyod/test/test_thresholds.py",
    "pyod/test/test_combination.py",
    "pyod/test/test_ad_engine.py",
]

OPTIONAL_TESTS = [
    "pyod/test/test_embedding.py",
    "pyod/test/test_audio.py",
    "pyod/test/test_suod.py",
    "pyod/test/test_xgbod.py",
    "pyod/test/test_torch_utility.py",
    "pyod/test/test_pyg_dominant.py",
    "pyod/test/test_pyg_cola.py",
    "pyod/test/test_pyg_conad.py",
]

COMMANDS = ["python", "pytest", "pyod", "pyod-install-skill", "playwright"]


def _rel_status(repo: Path, paths: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rel in paths:
        p = repo / rel
        rows.append({
            "path": rel,
            "exists": p.exists(),
            "kind": "dir" if p.is_dir() else "file" if p.is_file() else "missing",
        })
    return rows


def _read_pyproject(repo: Path) -> dict[str, Any]:
    path = repo / "pyproject.toml"
    if not path.is_file():
        return {"present": False, "error": "pyproject.toml not found"}
    if tomllib is None:
        return {"present": True, "error": "tomllib unavailable on this Python"}
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive reporting
        return {"present": True, "error": f"failed to parse: {exc}"}
    project = data.get("project", {})
    setuptools = data.get("tool", {}).get("setuptools", {})
    return {
        "present": True,
        "name": project.get("name"),
        "requires_python": project.get("requires-python"),
        "dynamic": project.get("dynamic", []),
        "scripts": project.get("scripts", {}),
        "optional_dependencies": sorted((project.get("optional-dependencies") or {}).keys()),
        "package_data": setuptools.get("package-data", {}),
        "package_find": setuptools.get("packages", {}).get("find", {}),
    }


def _command_status() -> list[dict[str, Any]]:
    return [{"command": cmd, "path": shutil.which(cmd)} for cmd in COMMANDS]


def _run_probe(cmd: list[str], cwd: Path, env: dict[str, str], timeout: int) -> dict[str, Any]:
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return {"command": cmd, "ok": False, "returncode": None, "stderr": "executable not found"}
    except subprocess.TimeoutExpired:
        return {"command": cmd, "ok": False, "returncode": None, "stderr": f"timed out after {timeout}s"}
    return {
        "command": cmd,
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-1000:],
        "stderr_tail": result.stderr[-1000:],
    }


def _import_checks(repo: Path, python: str, timeout: int) -> list[dict[str, Any]]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(repo) + (os.pathsep + existing if existing else "")
    probes = [
        [python, "-c", "import pyod; print(getattr(pyod, '__version__', 'unknown'))"],
        [python, "-m", "pyod.cli", "--help"],
        [python, "-m", "pyod.cli", "info"],
        [python, "scripts/regen_skill.py", "--check"],
    ]
    return [_run_probe(cmd, repo, env, timeout) for cmd in probes]


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path(args.repo_root).expanduser().resolve()
    report: dict[str, Any] = {
        "schema": "pyod.repo-maintenance.surface.v1",
        "repo_root": str(repo),
        "exists": repo.exists(),
        "core_files": _rel_status(repo, CORE_FILES),
        "relevant_tests": _rel_status(repo, RELEVANT_TESTS),
        "optional_tests": _rel_status(repo, OPTIONAL_TESTS),
        "pyproject": _read_pyproject(repo),
        "commands": _command_status(),
        "import_checks": [],
    }
    if args.import_check:
        report["import_checks"] = _import_checks(repo, args.python, args.timeout)
    missing_core = [row["path"] for row in report["core_files"] if not row["exists"]]
    missing_relevant_tests = [row["path"] for row in report["relevant_tests"] if not row["exists"]]
    failed_import_checks = [row for row in report["import_checks"] if not row.get("ok")]
    report["summary"] = {
        "missing_core_count": len(missing_core),
        "missing_relevant_test_count": len(missing_relevant_tests),
        "failed_import_check_count": len(failed_import_checks),
        "strict_ok": not missing_core and not failed_import_checks,
    }
    return report


def print_text(report: dict[str, Any]) -> None:
    print("PyOD repo maintenance surface check")
    print(f"Repo root: {report['repo_root']}")
    print(f"Exists:    {report['exists']}")
    print("\nCore files:")
    for row in report["core_files"]:
        mark = "OK" if row["exists"] else "MISSING"
        print(f"  [{mark:7}] {row['path']}")
    print("\nRelevant maintainer tests:")
    for row in report["relevant_tests"]:
        mark = "OK" if row["exists"] else "MISSING"
        print(f"  [{mark:7}] {row['path']}")
    if report["optional_tests"]:
        print("\nOptional-backend tests (presence only; missing extras may still skip):")
        for row in report["optional_tests"]:
            mark = "OK" if row["exists"] else "MISSING"
            print(f"  [{mark:7}] {row['path']}")
    print("\nPackage metadata:")
    pyproject = report["pyproject"]
    if pyproject.get("error"):
        print(f"  error: {pyproject['error']}")
    else:
        print(f"  name:              {pyproject.get('name')}")
        print(f"  requires-python:   {pyproject.get('requires_python')}")
        print(f"  scripts:           {', '.join(sorted(pyproject.get('scripts', {}))) or 'none'}")
        print(f"  optional extras:   {', '.join(pyproject.get('optional_dependencies', [])) or 'none'}")
        package_data = pyproject.get("package_data", {})
        skill_data = package_data.get("pyod.skills.od_expert")
        print(f"  od-expert data:    {skill_data if skill_data is not None else 'missing'}")
    print("\nCommand availability:")
    for row in report["commands"]:
        print(f"  {row['command']:<18} {row['path'] or 'not found'}")
    if report["import_checks"]:
        print("\nImport/CLI/generator probes:")
        for row in report["import_checks"]:
            mark = "OK" if row.get("ok") else "FAIL"
            print(f"  [{mark}] {' '.join(row['command'])}")
            if not row.get("ok") and row.get("stderr_tail"):
                print(f"       stderr: {row['stderr_tail'].strip()}")
    summary = report["summary"]
    print("\nSummary:")
    print(f"  missing core files:       {summary['missing_core_count']}")
    print(f"  missing relevant tests:   {summary['missing_relevant_test_count']}")
    print(f"  failed import checks:     {summary['failed_import_check_count']}")
    print(f"  strict-ok:                {summary['strict_ok']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only PyOD repository maintenance surface checker."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to a PyOD checkout to inspect (default: current directory).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--import-check",
        action="store_true",
        help="Run small read-only import/CLI/generator probes with --python.",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable for --import-check probes (default: current Python).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout in seconds for each import-check probe (default: 30).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if core files are missing or an import-check probe fails.",
    )
    args = parser.parse_args(argv)

    report = build_report(args)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    if args.strict and not report["summary"]["strict_ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
