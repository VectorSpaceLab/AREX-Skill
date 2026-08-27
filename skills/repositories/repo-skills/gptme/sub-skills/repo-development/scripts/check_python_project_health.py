#!/usr/bin/env python3
"""Inspect pyproject.toml, poetry.lock, package version, and entrypoint coherence."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any

import tomllib


@dataclass(frozen=True)
class Issue:
    severity: str
    message: str


@dataclass(frozen=True)
class Result:
    issues: tuple[Issue, ...]
    summary: tuple[str, ...]


def load_pyproject(root: Path) -> dict[str, Any]:
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        raise FileNotFoundError(f"missing pyproject.toml at {pyproject}")
    return tomllib.loads(pyproject.read_text(encoding="utf-8"))


def normalize_include_entry(entry: Any) -> str | None:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        path = entry.get("path")
        if isinstance(path, str):
            return path
    return None


def declared_scripts(pyproject: dict[str, Any]) -> dict[str, str]:
    project = pyproject.get("project", {})
    scripts = project.get("scripts", {})
    return scripts if isinstance(scripts, dict) else {}


def declared_entrypoints(pyproject: dict[str, Any]) -> dict[str, dict[str, str]]:
    project = pyproject.get("project", {})
    raw = project.get("entry-points", {})
    if not isinstance(raw, dict):
        return {}

    entrypoints: dict[str, dict[str, str]] = {}
    for group, value in raw.items():
        if isinstance(group, str) and isinstance(value, dict):
            entrypoints[group] = {
                name: target for name, target in value.items() if isinstance(name, str) and isinstance(target, str)
            }
    return entrypoints


def declared_version(pyproject: dict[str, Any]) -> tuple[str | None, str | None]:
    project = pyproject.get("project", {})
    tool_poetry = pyproject.get("tool", {}).get("poetry", {}) if isinstance(pyproject.get("tool"), dict) else {}
    project_version = project.get("version") if isinstance(project, dict) else None
    poetry_version = tool_poetry.get("version") if isinstance(tool_poetry, dict) else None
    return (
        project_version if isinstance(project_version, str) else None,
        poetry_version if isinstance(poetry_version, str) else None,
    )


def declared_name(pyproject: dict[str, Any]) -> str | None:
    project = pyproject.get("project", {})
    if not isinstance(project, dict):
        return None
    name = project.get("name")
    return name if isinstance(name, str) else None


def poetry_include_entries(pyproject: dict[str, Any]) -> set[str]:
    tool = pyproject.get("tool", {})
    poetry = tool.get("poetry", {}) if isinstance(tool, dict) else {}
    include = poetry.get("include", []) if isinstance(poetry, dict) else []
    if not isinstance(include, list):
        return set()
    values = {entry for entry in (normalize_include_entry(item) for item in include) if entry}
    return values


def module_target_candidates(root: Path, module: str) -> list[Path]:
    module_path = Path(*module.split("."))
    return [
        root / f"{module_path.as_posix()}.py",
        root / module_path / "__init__.py",
        root / module_path / "__main__.py",
    ]


def script_target_exists(root: Path, target: str) -> bool:
    if ":" not in target:
        return False
    module, _attr = target.split(":", 1)
    return any(candidate.is_file() for candidate in module_target_candidates(root, module))


def installed_distribution_state(package_name: str) -> tuple[str | None, dict[str, str], dict[str, str]]:
    try:
        dist = metadata.distribution(package_name)
    except metadata.PackageNotFoundError:
        return None, {}, {}

    console_scripts = {
        entry.name: entry.value
        for entry in dist.entry_points
        if entry.group == "console_scripts"
    }
    plugin_entries = {
        entry.name: entry.value
        for entry in dist.entry_points
        if entry.group == "gptme.plugins"
    }
    return dist.version, console_scripts, plugin_entries


def validate(root: Path, package_name: str) -> Result:
    issues: list[Issue] = []
    summary: list[str] = []

    pyproject = load_pyproject(root)
    project_name = declared_name(pyproject)
    project_version, poetry_version = declared_version(pyproject)
    scripts = declared_scripts(pyproject)
    entrypoints = declared_entrypoints(pyproject)
    include_entries = poetry_include_entries(pyproject)

    if project_name != package_name:
        issues.append(
            Issue(
                "error",
                f"project.name is {project_name!r}, expected {package_name!r}",
            )
        )

    if not project_version:
        issues.append(Issue("error", "project.version is missing"))
    elif poetry_version is not None and project_version != poetry_version:
        issues.append(
            Issue(
                "error",
                f"project.version {project_version!r} does not match tool.poetry.version {poetry_version!r}",
            )
        )

    lock_path = root / "poetry.lock"
    if not lock_path.is_file():
        issues.append(Issue("error", "poetry.lock is missing"))
    elif lock_path.stat().st_size == 0:
        issues.append(Issue("error", "poetry.lock is empty"))

    if "gptme/server/webui-dist" not in include_entries:
        issues.append(
            Issue(
                "error",
                "tool.poetry.include does not include gptme/server/webui-dist",
            )
        )
    if not any(entry.startswith("gptme/server/static") for entry in include_entries):
        issues.append(
            Issue(
                "error",
                "tool.poetry.include does not include gptme/server/static assets",
            )
        )

    for script_name, target in scripts.items():
        if not isinstance(target, str):
            continue
        if not script_target_exists(root, target):
            issues.append(
                Issue(
                    "error",
                    f"console script {script_name!r} points to missing target {target!r}",
                )
            )

    installed_version, installed_scripts, installed_plugins = installed_distribution_state(package_name)
    if installed_version is None:
        issues.append(Issue("warning", f"distribution {package_name!r} is not installed; installed entrypoint checks were skipped"))
    else:
        summary.append(f"installed distribution version: {installed_version}")
        if project_version and installed_version != project_version:
            issues.append(
                Issue(
                    "error",
                    f"installed distribution version {installed_version!r} does not match project.version {project_version!r}",
                )
            )

        for script_name, target in scripts.items():
            if not isinstance(target, str):
                continue
            installed_target = installed_scripts.get(script_name)
            if installed_target is None:
                issues.append(
                    Issue(
                        "error",
                        f"installed distribution is missing console_script {script_name!r}",
                    )
                )
            elif installed_target != target:
                issues.append(
                    Issue(
                        "error",
                        f"installed console_script {script_name!r} points to {installed_target!r}, expected {target!r}",
                    )
                )

        for group, declared_group in entrypoints.items():
            if group == "console_scripts":
                continue
            installed_group = installed_plugins if group == "gptme.plugins" else {}
            if not installed_group:
                issues.append(Issue("warning", f"installed distribution has no {group!r} entry points to compare"))
                continue
            for entry_name, target in declared_group.items():
                installed_target = installed_group.get(entry_name)
                if installed_target is None:
                    issues.append(
                        Issue(
                            "error",
                            f"installed distribution is missing {group!r} entry point {entry_name!r}",
                        )
                    )
                elif installed_target != target:
                    issues.append(
                        Issue(
                            "error",
                            f"installed {group!r} entry point {entry_name!r} points to {installed_target!r}, expected {target!r}",
                        )
                    )

    summary.append(f"project name: {project_name or 'unknown'}")
    summary.append(f"project version: {project_version or 'missing'}")
    summary.append(f"declared console scripts: {len(scripts)}")
    summary.append(f"declared plugin entry points: {sum(len(group) for group in entrypoints.values())}")
    summary.append(f"tool.poetry.include entries: {len(include_entries)}")

    return Result(tuple(issues), tuple(summary))


def render_text(result: Result) -> str:
    lines = ["Project health summary:"]
    for line in result.summary:
        lines.append(f"- {line}")

    if not result.issues:
        lines.append("\nNo project-health issues found.")
        return "\n".join(lines)

    lines.append("\nIssues:")
    for issue in result.issues:
        lines.append(f"- {issue.severity}: {issue.message}")
    return "\n".join(lines)


def render_json(result: Result) -> str:
    payload = {
        "summary": list(result.summary),
        "issues": [
            {"severity": issue.severity, "message": issue.message}
            for issue in result.issues
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."), help="Target gptme checkout root.")
    parser.add_argument("--package-name", default="gptme", help="Expected distribution/package name.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = validate(args.root.resolve(), args.package_name)
    output = render_json(result) if args.format == "json" else render_text(result)
    print(output)
    return 1 if any(issue.severity == "error" for issue in result.issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
