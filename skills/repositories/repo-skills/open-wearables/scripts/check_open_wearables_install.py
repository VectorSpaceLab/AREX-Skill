#!/usr/bin/env python3
"""Safe root checker for the Open Wearables repo skill.

The checker is read-only: it validates monorepo metadata, expected package
versions, required source directories, common service files, and frontend/MCP
metadata. It does not install dependencies, start services, call the network,
read real secrets, or write application files.

Examples:
  python check_open_wearables_install.py --repo-root .
  python check_open_wearables_install.py --repo-root . --json
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python <3.11 is not expected.
    tomllib = None  # type: ignore[assignment]


EXPECTED_FILES = [
    "README.md",
    "AGENTS.md",
    "Makefile",
    "docker-compose.yml",
    "backend/pyproject.toml",
    "backend/app/main.py",
    "backend/config/.env.example",
    "frontend/package.json",
    "frontend/.env.example",
    "mcp/pyproject.toml",
    "mcp/config/.env.example",
    "docs/docs.json",
]

EXPECTED_DIRS = [
    "backend/app/api/routes/v1",
    "backend/app/services/providers",
    "backend/tests",
    "frontend/src/routes",
    "frontend/src/hooks/api",
    "frontend/src/lib/api",
    "mcp/app/tools",
    "mcp/tests",
    "docs/dev-guides",
    "docs/providers",
]

EXPECTED_BACKEND_PACKAGE = {"name": "open-wearables", "version": "0.7.0", "requires-python": ">=3.13"}
EXPECTED_MCP_PACKAGE = {"name": "open-wearables-mcp", "version": "0.1.0", "requires-python": ">=3.13"}
EXPECTED_FRONTEND = {"name": "frontend-app", "version": "0.7.0"}


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    ok: list[str] = field(default_factory=list)
    info: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not self.errors

    def add_ok(self, message: str) -> None:
        self.ok.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)


def find_repo_root(start: Path | None) -> Path:
    if start is not None:
        return start.expanduser().resolve()
    cur = Path.cwd().resolve()
    for candidate in [cur, *cur.parents]:
        if (candidate / "backend" / "pyproject.toml").exists() and (candidate / "frontend" / "package.json").exists():
            return candidate
    return cur


def load_toml(path: Path, report: Report) -> dict[str, Any]:
    if tomllib is None:
        report.error("tomllib is unavailable; use Python 3.11+ for this checker")
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        report.error(f"missing TOML file: {path}")
    except tomllib.TOMLDecodeError as exc:
        report.error(f"invalid TOML in {path}: {exc}")
    return {}


def load_json(path: Path, report: Report) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        report.error(f"missing JSON file: {path}")
        return {}
    except json.JSONDecodeError as exc:
        report.error(f"invalid JSON in {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        report.error(f"expected object JSON in {path}")
        return {}
    return value


def check_paths(repo_root: Path, report: Report) -> None:
    missing_files = [path for path in EXPECTED_FILES if not (repo_root / path).is_file()]
    missing_dirs = [path for path in EXPECTED_DIRS if not (repo_root / path).is_dir()]
    if missing_files:
        for path in missing_files:
            report.error(f"missing expected file: {path}")
    else:
        report.add_ok(f"found {len(EXPECTED_FILES)} expected files")
    if missing_dirs:
        for path in missing_dirs:
            report.error(f"missing expected directory: {path}")
    else:
        report.add_ok(f"found {len(EXPECTED_DIRS)} expected directories")


def check_backend(repo_root: Path, report: Report) -> None:
    data = load_toml(repo_root / "backend" / "pyproject.toml", report)
    project = data.get("project", {}) if isinstance(data, dict) else {}
    for key, expected in EXPECTED_BACKEND_PACKAGE.items():
        actual = project.get(key)
        if actual != expected:
            report.error(f"backend project {key!r}: expected {expected!r}, found {actual!r}")
    deps = project.get("dependencies", [])
    dep_names = {str(dep).split(">=")[0].split("[")[0].lower() for dep in deps}
    for dep in ["fastapi", "sqlalchemy", "psycopg", "celery", "redis", "alembic", "boto3", "svix"]:
        if dep not in dep_names:
            report.warn(f"backend dependency {dep!r} was not found in project.dependencies")
    groups = data.get("dependency-groups", {}) if isinstance(data, dict) else {}
    for group in ["dev", "code-quality"]:
        if group not in groups:
            report.warn(f"backend dependency group {group!r} is missing")
    report.info["backend_package"] = {key: project.get(key) for key in EXPECTED_BACKEND_PACKAGE}
    report.add_ok("backend package metadata matches expected identity")


def check_frontend(repo_root: Path, report: Report) -> None:
    package = load_json(repo_root / "frontend" / "package.json", report)
    for key, expected in EXPECTED_FRONTEND.items():
        actual = package.get(key)
        if actual != expected:
            report.error(f"frontend package {key!r}: expected {expected!r}, found {actual!r}")
    engines = package.get("engines", {})
    if engines.get("node") != ">=22.0.0" or engines.get("pnpm") != ">=10.0.0":
        report.warn("frontend engines should remain Node >=22 and pnpm >=10")
    scripts = package.get("scripts", {})
    for script in ["dev", "build", "test", "lint", "format:check"]:
        if script not in scripts:
            report.warn(f"frontend package script {script!r} is missing")
    report.info["frontend_package"] = {
        "name": package.get("name"),
        "version": package.get("version"),
        "packageManager": package.get("packageManager"),
    }
    report.add_ok("frontend package metadata is present")


def check_mcp(repo_root: Path, report: Report) -> None:
    data = load_toml(repo_root / "mcp" / "pyproject.toml", report)
    project = data.get("project", {}) if isinstance(data, dict) else {}
    for key, expected in EXPECTED_MCP_PACKAGE.items():
        actual = project.get(key)
        if actual != expected:
            report.error(f"MCP project {key!r}: expected {expected!r}, found {actual!r}")
    start = (project.get("scripts") or {}).get("start")
    if start != "app.main:main":
        report.error(f"MCP start script should be app.main:main, found {start!r}")
    report.info["mcp_package"] = {key: project.get(key) for key in EXPECTED_MCP_PACKAGE} | {"start": start}
    report.add_ok("MCP package metadata matches expected identity")


def check_docs(repo_root: Path, report: Report) -> None:
    docs = load_json(repo_root / "docs" / "docs.json", report)
    tabs = docs.get("navigation", {}).get("tabs", []) if isinstance(docs, dict) else []
    tab_names = [tab.get("tab") for tab in tabs if isinstance(tab, dict)]
    if "API Reference" not in tab_names:
        report.error("docs/docs.json is missing the API Reference tab")
    else:
        report.add_ok("docs navigation contains API Reference tab")
    report.info["docs_tabs"] = tab_names


def check_tools(report: Report) -> None:
    for name in ["uv", "node", "docker"]:
        found = shutil.which(name)
        report.info[f"tool_{name}"] = bool(found)
        if not found:
            report.warn(f"{name!r} is not on PATH; related native checks may need setup")
    if shutil.which("docker"):
        try:
            completed = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True, timeout=10)
        except Exception as exc:  # noqa: BLE001 - diagnostic only.
            report.warn(f"could not query docker compose version: {exc}")
        else:
            if completed.returncode == 0:
                report.info["docker_compose"] = completed.stdout.strip()
            else:
                report.warn("docker compose is not available even though docker is on PATH")


def print_human(report: Report) -> None:
    print("Open Wearables root checker")
    for key, value in sorted(report.info.items()):
        print(f"info: {key}={value}")
    for message in report.ok:
        print(f"ok: {message}")
    for message in report.warnings:
        print(f"warning: {message}")
    for message in report.errors:
        print(f"error: {message}")
    print("status:", "pass" if report.passed else "fail")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe static checks for an Open Wearables checkout.")
    parser.add_argument("--repo-root", type=Path, default=None, help="Path to the Open Wearables checkout (default: auto-detect).")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable output.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    args = parser.parse_args()

    report = Report()
    repo_root = find_repo_root(args.repo_root)
    report.info["repo_root"] = str(repo_root)
    check_paths(repo_root, report)
    check_backend(repo_root, report)
    check_frontend(repo_root, report)
    check_mcp(repo_root, report)
    check_docs(repo_root, report)
    check_tools(report)

    if args.json:
        print(json.dumps({"ok": report.passed, "errors": report.errors, "warnings": report.warnings, "info": report.info}, indent=2, sort_keys=True))
    else:
        print_human(report)
    if report.errors or (args.strict and report.warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
