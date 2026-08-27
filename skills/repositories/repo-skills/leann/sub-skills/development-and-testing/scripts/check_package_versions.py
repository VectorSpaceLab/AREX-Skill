#!/usr/bin/env python3
"""Read-only LEANN monorepo package-version consistency checker."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]


INTERNAL_PREFIXES = ("leann", "leann-")
DEPENDENCY_NAME = re.compile(r"^\s*([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?")
EXACT_VERSION = re.compile(r"==\s*([A-Za-z0-9.+!_-]+)")
MIN_VERSION = re.compile(r">=\s*([A-Za-z0-9.+!_-]+)")
NUMERIC_VERSION = re.compile(r"^[vV]?(\d+(?:\.\d+)*)$")


@dataclass(frozen=True)
class Manifest:
    path: Path
    name: str
    version: str
    dependencies: tuple[str, ...]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read LEANN package pyproject.toml files, report component version skew, "
            "and validate internal exact/minimum dependency constraints. No files are modified."
        )
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        metavar="PATH",
        help=(
            "LEANN repository root containing pyproject.toml and packages/ "
            "(default: current directory)"
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON report",
    )
    return parser.parse_args(argv)


def canonicalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def collect_dependencies(project: dict[str, Any]) -> tuple[str, ...]:
    dependencies: list[str] = []
    raw_dependencies = project.get("dependencies", [])
    if isinstance(raw_dependencies, list):
        dependencies.extend(str(item) for item in raw_dependencies)

    optional = project.get("optional-dependencies", {})
    if isinstance(optional, dict):
        for group in sorted(optional):
            values = optional[group]
            if isinstance(values, list):
                dependencies.extend(str(item) for item in values)
    return tuple(dependencies)


def load_manifest(path: Path) -> Manifest:
    if tomllib is None:
        raise RuntimeError(
            "TOML parser unavailable: use Python 3.11+ or install the 'tomli' "
            "package for Python 3.10"
        )
    try:
        with path.open("rb") as stream:
            data = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"cannot parse {path}: {exc}") from exc

    project = data.get("project")
    if not isinstance(project, dict):
        raise ValueError(f"missing [project] table in {path}")
    name = project.get("name")
    version = project.get("version")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"missing project.name in {path}")
    if not isinstance(version, str) or not version.strip():
        raise ValueError(f"missing project.version in {path}")

    return Manifest(
        path=path,
        name=canonicalize(name),
        version=version.strip(),
        dependencies=collect_dependencies(project),
    )


def numeric_version(value: str) -> tuple[int, ...] | None:
    match = NUMERIC_VERSION.fullmatch(value)
    if not match:
        return None
    return tuple(int(part) for part in match.group(1).split("."))


def version_at_least(actual: str, minimum: str) -> bool | None:
    actual_parts = numeric_version(actual)
    minimum_parts = numeric_version(minimum)
    if actual_parts is None or minimum_parts is None:
        return None
    width = max(len(actual_parts), len(minimum_parts))
    return actual_parts + (0,) * (width - len(actual_parts)) >= minimum_parts + (0,) * (
        width - len(minimum_parts)
    )


def dependency_name(requirement: str) -> str | None:
    match = DEPENDENCY_NAME.match(requirement)
    return canonicalize(match.group(1)) if match else None


def relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def inspect_repository(repo_root: Path) -> tuple[dict[str, Any], int]:
    root = repo_root.expanduser().resolve()
    root_manifest_path = root / "pyproject.toml"
    packages_dir = root / "packages"

    fatal: list[str] = []
    if not root.is_dir():
        fatal.append(f"repository root is not a directory: {root}")
    if not root_manifest_path.is_file():
        fatal.append(f"missing repository pyproject.toml: {root_manifest_path}")
    if not packages_dir.is_dir():
        fatal.append(f"missing packages directory: {packages_dir}")
    if fatal:
        return {"repo_root": str(root), "status": "invalid", "errors": fatal}, 2

    paths = [root_manifest_path, *sorted(packages_dir.glob("*/pyproject.toml"))]
    manifests: list[Manifest] = []
    for path in paths:
        try:
            manifests.append(load_manifest(path))
        except (RuntimeError, ValueError) as exc:
            fatal.append(str(exc))
    if fatal:
        return {"repo_root": str(root), "status": "invalid", "errors": fatal}, 2

    root_manifest = next(item for item in manifests if item.path == root_manifest_path)
    components = sorted(
        (
            item
            for item in manifests
            if item.path != root_manifest_path and item.name.startswith(INTERNAL_PREFIXES)
        ),
        key=lambda item: item.name,
    )
    if not components:
        return {
            "repo_root": str(root),
            "status": "invalid",
            "errors": ["no LEANN component pyproject.toml files found under packages/"],
        }, 2

    component_by_name = {item.name: item for item in components}
    errors: list[str] = []
    warnings: list[str] = []

    versions: dict[str, list[str]] = {}
    for component in components:
        versions.setdefault(component.version, []).append(component.name)
    if len(versions) > 1:
        rendered = "; ".join(
            f"{version}: {', '.join(sorted(names))}" for version, names in sorted(versions.items())
        )
        errors.append(f"component version skew detected ({rendered})")

    constraints: list[dict[str, str]] = []
    for owner in manifests:
        for requirement in owner.dependencies:
            target_name = dependency_name(requirement)
            if target_name not in component_by_name:
                continue
            target = component_by_name[target_name]
            record = {
                "owner": owner.name,
                "target": target_name,
                "requirement": requirement,
                "target_version": target.version,
            }
            constraints.append(record)

            exact = EXACT_VERSION.search(requirement)
            if exact and exact.group(1) != target.version:
                errors.append(
                    f"{owner.name} requires {target_name}=={exact.group(1)}, "
                    f"but {relative(target.path, root)} declares {target.version}"
                )
                continue

            minimum = MIN_VERSION.search(requirement)
            if minimum:
                verdict = version_at_least(target.version, minimum.group(1))
                if verdict is False:
                    errors.append(
                        f"{owner.name} requires {target_name}>={minimum.group(1)}, "
                        f"but {relative(target.path, root)} declares {target.version}"
                    )
                elif verdict is None:
                    warnings.append(
                        f"could not compare non-numeric constraint {requirement!r} "
                        f"against {target.version!r}"
                    )

    report = {
        "repo_root": str(root),
        "status": "fail" if errors else "ok",
        "workspace": {
            "name": root_manifest.name,
            "version": root_manifest.version,
            "path": relative(root_manifest.path, root),
            "alignment_scope": "excluded (workspace metadata is not a release component)",
        },
        "components": [
            {
                "name": item.name,
                "version": item.version,
                "path": relative(item.path, root),
            }
            for item in components
        ],
        "internal_constraints": constraints,
        "errors": errors,
        "warnings": warnings,
        "read_only": True,
    }
    return report, 1 if errors else 0


def render_text(report: dict[str, Any]) -> str:
    lines = [f"Repository: {report['repo_root']}"]
    if report.get("workspace"):
        workspace = report["workspace"]
        lines.append(
            f"Workspace:  {workspace['name']} {workspace['version']} "
            f"({workspace['path']}; {workspace['alignment_scope']})"
        )
    components = report.get("components", [])
    if components:
        lines.append("Components:")
        width = max(len(item["name"]) for item in components)
        for item in components:
            lines.append(
                f"  {item['name']:<{width}}  {item['version']:<12}  {item['path']}"
            )
    for warning in report.get("warnings", []):
        lines.append(f"WARNING: {warning}")
    for error in report.get("errors", []):
        lines.append(f"ERROR: {error}")
    status = report.get("status", "invalid").upper()
    lines.append(f"Result: {status} (read-only; no files modified)")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report, exit_code = inspect_repository(Path(args.repo_root))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_text(report))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
