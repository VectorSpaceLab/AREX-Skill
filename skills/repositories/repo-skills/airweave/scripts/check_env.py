#!/usr/bin/env python3
"""Quick, safe Airweave repository sanity checks.

This helper is intentionally non-mutating. It verifies that the generated skill
 tree is present, inspects package metadata, and can optionally try a backend
 import from the checked-out repository.

Examples:
    python skills/disco/airweave/scripts/check_env.py --repo-root /path/to/airweave
    python skills/disco/airweave/scripts/check_env.py --repo-root /path/to/airweave --backend-import
    python skills/disco/airweave/scripts/check_env.py --repo-root /path/to/airweave --json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from shutil import which
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.11+ should have it
    tomllib = None  # type: ignore[assignment]


REPO_MARKERS = (
    Path("backend/pyproject.toml"),
    Path("frontend/package.json"),
    Path("connect/package.json"),
    Path("mcp/package.json"),
    Path("monke/README.md"),
)

DEFAULT_SKILL_ROOT = Path("skills/disco/airweave")

EXPECTED_FILES = (
    Path("SKILL.md"),
    Path("references/overview.md"),
    Path("references/troubleshooting.md"),
    Path("references/repo-provenance.md"),
    Path("references/repo-routing-metadata.json"),
    Path("scripts/check_env.py"),
    Path("sub-skills/local-development/SKILL.md"),
    Path("sub-skills/local-development/references/local-stack.md"),
    Path("sub-skills/local-development/references/troubleshooting.md"),
    Path("sub-skills/local-development/scripts/local-stack.sh"),
    Path("sub-skills/backend-api/SKILL.md"),
    Path("sub-skills/backend-api/references/api-reference.md"),
    Path("sub-skills/backend-api/references/workflows.md"),
    Path("sub-skills/backend-api/references/troubleshooting.md"),
    Path("sub-skills/backend-api/scripts/agentic_search_stream.py"),
    Path("sub-skills/source-connectors/SKILL.md"),
    Path("sub-skills/source-connectors/references/source-registry.md"),
    Path("sub-skills/source-connectors/references/auth-and-config.md"),
    Path("sub-skills/source-connectors/references/browse-tree.md"),
    Path("sub-skills/source-connectors/references/troubleshooting.md"),
    Path("sub-skills/frontend-dashboard/SKILL.md"),
    Path("sub-skills/frontend-dashboard/references/api-client.md"),
    Path("sub-skills/frontend-dashboard/references/search-ui.md"),
    Path("sub-skills/frontend-dashboard/references/collections-and-orgs.md"),
    Path("sub-skills/frontend-dashboard/references/troubleshooting.md"),
    Path("sub-skills/connect-widget/SKILL.md"),
    Path("sub-skills/connect-widget/references/widget-overview.md"),
    Path("sub-skills/connect-widget/references/messaging-contract.md"),
    Path("sub-skills/connect-widget/references/oauth-and-modes.md"),
    Path("sub-skills/connect-widget/references/troubleshooting.md"),
    Path("sub-skills/mcp-search/SKILL.md"),
    Path("sub-skills/mcp-search/references/mcp-overview.md"),
    Path("sub-skills/mcp-search/references/transport-and-tools.md"),
    Path("sub-skills/mcp-search/references/auth-and-troubleshooting.md"),
    Path("sub-skills/mcp-search/scripts/mcp-smoke.sh"),
    Path("sub-skills/monke-e2e/SKILL.md"),
    Path("sub-skills/monke-e2e/references/overview.md"),
    Path("sub-skills/monke-e2e/references/connector-registry.md"),
    Path("sub-skills/monke-e2e/references/config-and-auth.md"),
    Path("sub-skills/monke-e2e/references/troubleshooting.md"),
    Path("sub-skills/monke-e2e/scripts/monke-list-connectors.sh"),
)


def find_repo_root(start: Path) -> Path | None:
    """Find the Airweave repo root by walking up from a start directory."""
    for candidate in [start, *start.parents]:
        if all((candidate / marker).exists() for marker in REPO_MARKERS):
            return candidate
    return None


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_toml(path: Path) -> dict[str, Any]:
    if tomllib is None:
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def package_summary(path: Path) -> str:
    """Return a short package summary from JSON or TOML metadata."""
    try:
        if path.suffix == ".json":
            data = read_json(path)
            name = data.get("name", "<unknown>")
            version = data.get("version", "<unknown>")
            return f"{name} {version}"
        if path.name == "pyproject.toml":
            data = read_toml(path)
            if isinstance(data, dict):
                project = data.get("project", {})
                if isinstance(project, dict) and project:
                    name = project.get("name", "<unknown>")
                    version = project.get("version", "<unknown>")
                    return f"{name} {version}"
                poetry = data.get("tool", {}).get("poetry", {}) if isinstance(data.get("tool"), dict) else {}
                if isinstance(poetry, dict) and poetry:
                    name = poetry.get("name", "<unknown>")
                    version = poetry.get("version", "<unknown>")
                    return f"{name} {version}"
    except Exception as exc:  # pragma: no cover - defensive reporting
        return f"<unreadable: {exc}>"
    return "<unknown>"


def check_expected_files(skill_root: Path) -> list[Path]:
    """Return a list of expected runtime files that are missing."""
    missing: list[Path] = []
    for rel_path in EXPECTED_FILES:
        if not (skill_root / rel_path).exists():
            missing.append(rel_path)
    return missing


def run_backend_import(root: Path) -> tuple[bool, str]:
    """Attempt to import the backend package from the repository."""
    backend_dir = root / "backend"
    if not backend_dir.exists():
        return False, "backend/ directory not found"

    command = [
        sys.executable,
        "-c",
        "import airweave; print(airweave.__file__)",
    ]
    proc = subprocess.run(
        command,
        cwd=backend_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        return True, proc.stdout.strip() or "import succeeded"
    details = proc.stderr.strip() or proc.stdout.strip() or "unknown error"
    return False, details


def print_human(report: dict[str, Any]) -> None:
    """Render a readable status summary."""
    print(f"Airweave repo root: {report['repo_root']}")
    print(f"Airweave skill root: {report['skill_root']}")
    print("Packages:")
    for label, value in report["packages"].items():
        print(f"  - {label}: {value}")

    print("Skill tree:")
    if report["missing_files"]:
        for rel_path in report["missing_files"]:
            print(f"  - missing: {rel_path}")
    else:
        print("  - all expected runtime files are present")

    if report.get("backend_import") is not None:
        backend_import = report["backend_import"]
        status = "ok" if backend_import["ok"] else "failed"
        print(f"Backend import: {status}")
        print(f"  - {backend_import['message']}")

    print("Commands:")
    for cmd, value in report["commands"].items():
        print(f"  - {cmd}: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Quick Airweave repo sanity checks")
    parser.add_argument("--repo-root", help="Path to the Airweave repository root")
    parser.add_argument(
        "--skill-root",
        default=str(DEFAULT_SKILL_ROOT),
        help="Path to the generated Airweave skill root relative to the repo root",
    )
    parser.add_argument(
        "--backend-import",
        action="store_true",
        help="Attempt a backend import from the repository's backend/ directory",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human-readable output",
    )
    args = parser.parse_args()

    start = Path(args.repo_root).expanduser().resolve() if args.repo_root else Path.cwd().resolve()
    repo_root = start if args.repo_root else find_repo_root(start)
    if repo_root is None:
        print(
            "Could not find the Airweave repo root. Pass --repo-root PATH or run from within the checkout.",
            file=sys.stderr,
        )
        return 2

    skill_root_input = Path(args.skill_root).expanduser()
    skill_root = skill_root_input if skill_root_input.is_absolute() else (repo_root / skill_root_input)

    packages = {
        "backend": package_summary(repo_root / "backend/pyproject.toml"),
        "frontend": package_summary(repo_root / "frontend/package.json"),
        "connect": package_summary(repo_root / "connect/package.json"),
        "mcp": package_summary(repo_root / "mcp/package.json"),
    }

    commands = {
        "python": which("python") or which("python3") or "<not found>",
        "node": which("node") or "<not found>",
        "npm": which("npm") or "<not found>",
        "git": which("git") or "<not found>",
    }

    missing_files = check_expected_files(skill_root)
    backend_import: dict[str, Any] | None = None
    if args.backend_import:
        ok, message = run_backend_import(repo_root)
        backend_import = {"ok": ok, "message": message}

    report: dict[str, Any] = {
        "repo_root": str(repo_root),
        "skill_root": str(skill_root),
        "packages": packages,
        "commands": commands,
        "missing_files": [str(path) for path in missing_files],
        "backend_import": backend_import,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)

    if missing_files:
        return 1
    if backend_import is not None and not backend_import["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
