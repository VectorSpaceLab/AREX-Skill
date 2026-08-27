#!/usr/bin/env python3
"""Static/read-only contract check for the Observal Python CLI.

The helper imports the Typer application, converts it to Click metadata, and
checks that the repo still exposes the command groups and bundled skills that
this sub-skill routes to. It does not call the network, authenticate, mutate
CLI config, run command callbacks, or synchronize installed skills.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

EXPECTED_ROOT_COMMANDS = {
    "api",
    "scan",
    "outdated",
    "reconcile",
    "auth",
    "config",
    "registry",
    "inbox",
    "agent",
    "team",
    "ops",
    "admin",
    "self",
    "doctor",
    "server",
}

EXPECTED_REGISTRY_COMMANDS = {"mcp", "skill", "hook", "prompt", "sandbox", "models", "version", "recommend", "bulk"}
EXPECTED_AGENT_COMMANDS = {
    "create",
    "bulk-create",
    "list",
    "my",
    "show",
    "install",
    "archive",
    "unarchive",
    "delete",
    "init",
    "add",
    "build",
    "publish",
    "release",
    "versions",
    "pull",
    "co-authors",
    "transfer-owner",
}
EXPECTED_BUNDLED_SKILLS = {
    "observal",
    "observal-admin",
    "observal-advanced",
    "observal-agents",
    "observal-ops",
    "observal-registry",
}


def find_repo_root(value: str) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "observal_cli" / "main.py").is_file():
            return candidate
    return cwd


def prepend_import_paths(repo_root: Path) -> None:
    for path in (repo_root / "packages" / "observal-shared", repo_root):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)


def command_names(command: Any) -> set[str]:
    commands = getattr(command, "commands", {}) or {}
    return set(commands)


def child(command: Any, name: str) -> Any | None:
    return (getattr(command, "commands", {}) or {}).get(name)


def bundled_skill_rows(repo_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    skills_root = repo_root / "observal_cli" / "skills"
    for name in sorted(EXPECTED_BUNDLED_SKILLS):
        skill_md = skills_root / name / "SKILL.md"
        refs = sorted(str(p.relative_to(skills_root / name)) for p in (skills_root / name).glob("references/*.md"))
        rows.append(
            {
                "name": name,
                "skill_md": skill_md.is_file(),
                "reference_count": len(refs),
                "references": refs,
            }
        )
    return rows


def load_cli(repo_root: Path) -> dict[str, Any]:
    prepend_import_paths(repo_root)
    from typer.main import get_command  # noqa: PLC0415
    from observal_cli.main import app  # noqa: PLC0415

    root = get_command(app)
    root_commands = command_names(root)
    registry = child(root, "registry")
    agent = child(root, "agent")
    doctor = child(root, "doctor")
    ops = child(root, "ops")
    server = child(root, "server")

    rows = bundled_skill_rows(repo_root)
    summary = {
        "missing_root_commands": sorted(EXPECTED_ROOT_COMMANDS - root_commands),
        "extra_root_commands": sorted(root_commands - EXPECTED_ROOT_COMMANDS),
        "missing_registry_commands": sorted(EXPECTED_REGISTRY_COMMANDS - command_names(registry)) if registry else sorted(EXPECTED_REGISTRY_COMMANDS),
        "missing_agent_commands": sorted(EXPECTED_AGENT_COMMANDS - command_names(agent)) if agent else sorted(EXPECTED_AGENT_COMMANDS),
        "missing_bundled_skills": [row["name"] for row in rows if not row["skill_md"]],
    }
    payload = {
        "ok": not any(summary.values()),
        "root_command_count": len(root_commands),
        "root_commands": sorted(root_commands),
        "registry_commands": sorted(command_names(registry)) if registry else [],
        "agent_commands": sorted(command_names(agent)) if agent else [],
        "doctor_commands": sorted(command_names(doctor)) if doctor else [],
        "ops_commands": sorted(command_names(ops)) if ops else [],
        "server_commands": sorted(command_names(server)) if server else [],
        "bundled_skills": rows,
        "summary": summary,
    }
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Observal CLI command and bundled-skill contract.")
    parser.add_argument("--repo-root", default="", help="Path to an Observal checkout; default searches parents.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    repo_root = find_repo_root(args.repo_root)
    try:
        payload = load_cli(repo_root)
        status = 0 if payload["ok"] else 1
    except Exception as exc:  # noqa: BLE001 - report import/metadata failures as JSON.
        payload = {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "hint": "Run from an Observal checkout with CLI dependencies installed, or pass --repo-root.",
        }
        status = 1

    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
