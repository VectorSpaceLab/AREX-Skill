#!/usr/bin/env python3
"""Safely inspect an installed CrewAI CLI and project layout.

The script imports ``crewai_cli.cli`` and reads Click command metadata. It can
also inspect marker files in a project directory. It does not run crews, flows,
login, deploy, contact networks, read secrets, or execute custom project tools.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:  # pragma: no cover
        tomllib = None  # type: ignore[assignment]


def _command_tree(command: Any, prefix: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    commands = getattr(command, "commands", None)
    if not commands:
        return rows

    for name in sorted(commands):
        subcommand = commands[name]
        path = (*prefix, name)
        params: list[str] = []
        for param in getattr(subcommand, "params", []) or []:
            option_names = getattr(param, "opts", None) or [getattr(param, "name", "")]
            secondary = getattr(param, "secondary_opts", None) or []
            names = [item for item in [*option_names, *secondary] if item]
            if names:
                params.append("/".join(names))
        rows.append(
            {
                "path": " ".join(path),
                "help": (getattr(subcommand, "help", None) or "").strip(),
                "params": params,
            }
        )
        rows.extend(_command_tree(subcommand, path))
    return rows


def inspect_cli() -> dict[str, Any]:
    """Return Click command metadata for the installed CrewAI CLI."""
    try:
        from crewai_cli.cli import crewai
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": f"Could not import crewai_cli.cli: {exc}",
            "commands": [],
        }

    return {
        "ok": True,
        "commands": _command_tree(crewai),
    }


def _normalize_package_name(project_name: str) -> str:
    folder = project_name.replace(" ", "_").replace("-", "_").lower()
    return re.sub(r"[^a-zA-Z0-9_]", "", folder)


def _load_pyproject(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, "pyproject.toml not found"
    if tomllib is None:
        return None, "tomllib/tomli is not available"
    try:
        return tomllib.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:  # noqa: BLE001
        return None, f"pyproject.toml could not be parsed: {exc}"


def inspect_project(project_root: Path) -> dict[str, Any]:
    """Inspect CrewAI project marker files without importing project code."""
    root = project_root.resolve()
    pyproject_path = root / "pyproject.toml"
    pyproject, pyproject_error = _load_pyproject(pyproject_path)

    project_name: str | None = None
    normalized_name: str | None = None
    declared_type: str | None = None
    scripts: dict[str, str] = {}
    if pyproject:
        project = pyproject.get("project") or {}
        if isinstance(project, dict):
            project_name = project.get("name") if isinstance(project.get("name"), str) else None
            if project_name:
                normalized_name = _normalize_package_name(project_name)
            raw_scripts = project.get("scripts") or {}
            if isinstance(raw_scripts, dict):
                scripts = {str(key): str(value) for key, value in raw_scripts.items()}
        tool = pyproject.get("tool") or {}
        if isinstance(tool, dict):
            crewai_tool = tool.get("crewai") or {}
            if isinstance(crewai_tool, dict):
                declared_type = crewai_tool.get("type") if isinstance(crewai_tool.get("type"), str) else None

    has_crew_jsonc = (root / "crew.jsonc").is_file()
    has_crew_json = (root / "crew.json").is_file()
    has_agents_dir = (root / "agents").is_dir()
    has_uv_lock = (root / "uv.lock").is_file()
    has_poetry_lock = (root / "poetry.lock").is_file()

    package_dir = root / "src" / normalized_name if normalized_name else None
    likely_type = "unknown"
    if declared_type == "flow":
        likely_type = "flow"
    elif has_crew_jsonc or has_crew_json:
        likely_type = "json-crew"
    elif declared_type == "crew":
        likely_type = "classic-crew"

    checks: list[dict[str, str]] = []

    def add_check(name: str, status: bool, detail: str) -> None:
        checks.append({"name": name, "status": "ok" if status else "warn", "detail": detail})

    add_check("project-root", pyproject_path.is_file(), "pyproject.toml present at project root")
    if pyproject_error:
        add_check("pyproject-parse", False, pyproject_error)
    if likely_type == "json-crew":
        add_check("json-crew-file", has_crew_jsonc or has_crew_json, "crew.jsonc or crew.json present")
        add_check("agents-dir", has_agents_dir, "agents/ directory present")
    if likely_type == "classic-crew":
        package = package_dir or root / "src" / "<project-name>"
        add_check("package-dir", package_dir is not None and package_dir.is_dir(), f"expected {package}")
        add_check("crew-py", package_dir is not None and (package_dir / "crew.py").is_file(), "classic crew.py present")
        add_check("agents-yaml", package_dir is not None and (package_dir / "config" / "agents.yaml").is_file(), "config/agents.yaml present")
        add_check("tasks-yaml", package_dir is not None and (package_dir / "config" / "tasks.yaml").is_file(), "config/tasks.yaml present")
        for script_name in ("run_crew", "train", "replay", "test"):
            add_check(f"script-{script_name}", script_name in scripts, f"[project.scripts].{script_name} present")
    if likely_type == "flow":
        package = package_dir or root / "src" / "<project-name>"
        add_check("package-dir", package_dir is not None and package_dir.is_dir(), f"expected {package}")
        add_check("main-py", package_dir is not None and (package_dir / "main.py").is_file(), "flow main.py present")
        for script_name in ("kickoff", "plot", "run_with_trigger"):
            add_check(f"script-{script_name}", script_name in scripts, f"[project.scripts].{script_name} present")
    add_check("lockfile", has_uv_lock or has_poetry_lock, "uv.lock or poetry.lock present for deploy")

    return {
        "root": str(root),
        "project_name": project_name,
        "normalized_package": normalized_name,
        "declared_type": declared_type,
        "likely_type": likely_type,
        "markers": {
            "pyproject.toml": pyproject_path.is_file(),
            "crew.jsonc": has_crew_jsonc,
            "crew.json": has_crew_json,
            "agents/": has_agents_dir,
            "uv.lock": has_uv_lock,
            "poetry.lock": has_poetry_lock,
        },
        "scripts": scripts,
        "checks": checks,
    }


def _print_text(payload: dict[str, Any]) -> None:
    if "commands" in payload:
        if not payload.get("ok"):
            print(payload.get("error", "CLI inspection failed"), file=sys.stderr)
            return
        for row in payload["commands"]:
            params = ", ".join(row["params"])
            suffix = f" [{params}]" if params else ""
            print(f"{row['path']}: {row['help']}{suffix}")
        return

    print(f"Project: {payload['root']}")
    print(f"Likely type: {payload['likely_type']}")
    if payload.get("project_name"):
        print(f"Project name: {payload['project_name']}")
    if payload.get("declared_type"):
        print(f"Declared [tool.crewai].type: {payload['declared_type']}")
    print("Markers:")
    for marker, present in payload["markers"].items():
        print(f"  {'ok' if present else '--'} {marker}")
    print("Checks:")
    for check in payload["checks"]:
        print(f"  {check['status']}: {check['name']} - {check['detail']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely inspect CrewAI CLI metadata and project marker files.")
    parser.add_argument("--commands", action="store_true", help="List installed crewai Click commands and options.")
    parser.add_argument("--project", type=Path, help="Inspect a CrewAI project directory without importing project code.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args(argv)

    if not args.commands and args.project is None:
        parser.error("choose --commands and/or --project")

    outputs: list[dict[str, Any]] = []
    if args.commands:
        outputs.append({"cli": inspect_cli()})
    if args.project is not None:
        outputs.append({"project": inspect_project(args.project)})

    if args.json:
        if len(outputs) == 1:
            print(json.dumps(outputs[0], indent=2, sort_keys=True))
        else:
            print(json.dumps(outputs, indent=2, sort_keys=True))
    else:
        for index, output in enumerate(outputs):
            if index:
                print()
            key, payload = next(iter(output.items()))
            print(f"[{key}]")
            _print_text(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
