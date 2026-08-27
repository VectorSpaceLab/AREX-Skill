#!/usr/bin/env python3
"""Inspect LangChain package metadata without importing or mutating the repo."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path
from typing import Any


PROJECT_ROOT_MARKERS = {"libs"}


def load_pyproject(package_dir: Path) -> dict[str, Any]:
    """Load package metadata from `pyproject.toml`.

    Args:
        package_dir: Directory expected to contain `pyproject.toml`.

    Returns:
        Parsed TOML data.

    Raises:
        FileNotFoundError: If `pyproject.toml` does not exist.
        tomllib.TOMLDecodeError: If the TOML file is invalid.
    """
    pyproject_path = package_dir / "pyproject.toml"
    with pyproject_path.open("rb") as pyproject_file:
        return tomllib.load(pyproject_file)


def sorted_mapping_keys(value: object) -> list[str]:
    """Return sorted keys for mapping-like metadata values."""
    if isinstance(value, dict):
        return sorted(str(key) for key in value)
    return []


def summarize_package(package_dir: Path, data: dict[str, Any]) -> dict[str, Any]:
    """Build a stable summary of package-local metadata.

    Args:
        package_dir: Package directory being inspected.
        data: Parsed `pyproject.toml` data.

    Returns:
        JSON-serializable package summary.
    """
    project = data.get("project", {})
    dependency_groups = data.get("dependency-groups", {})
    tool = data.get("tool", {})
    uv_config = tool.get("uv", {}) if isinstance(tool, dict) else {}
    optional_dependencies = project.get("optional-dependencies", {}) if isinstance(project, dict) else {}

    return {
        "package_dir": str(package_dir),
        "pyproject": str(package_dir / "pyproject.toml"),
        "has_uv_lock": (package_dir / "uv.lock").exists(),
        "has_makefile": (package_dir / "Makefile").exists(),
        "project_name": project.get("name") if isinstance(project, dict) else None,
        "version": project.get("version") if isinstance(project, dict) else None,
        "requires_python": project.get("requires-python") if isinstance(project, dict) else None,
        "dependency_count": len(project.get("dependencies", []))
        if isinstance(project.get("dependencies"), list)
        else 0,
        "dependency_groups": sorted_mapping_keys(dependency_groups),
        "optional_extras": sorted_mapping_keys(optional_dependencies),
        "uv_sources": sorted_mapping_keys(uv_config.get("sources") if isinstance(uv_config, dict) else {}),
        "ruff_configured": "ruff" in tool if isinstance(tool, dict) else False,
        "mypy_configured": "mypy" in tool if isinstance(tool, dict) else False,
        "pytest_configured": "pytest" in tool if isinstance(tool, dict) else False,
    }


def print_text_summary(summary: dict[str, Any]) -> None:
    """Print a human-readable package summary."""
    print(f"Package directory: {summary['package_dir']}")
    print(f"Project name: {summary['project_name'] or '<missing>'}")
    print(f"Version: {summary['version'] or '<missing>'}")
    print(f"Requires Python: {summary['requires_python'] or '<missing>'}")
    print(f"Has uv.lock: {summary['has_uv_lock']}")
    print(f"Has Makefile: {summary['has_makefile']}")
    print(f"Runtime dependency count: {summary['dependency_count']}")
    print("Dependency groups: " + ", ".join(summary["dependency_groups"]) if summary["dependency_groups"] else "Dependency groups: <none>")
    print("Optional extras: " + ", ".join(summary["optional_extras"]) if summary["optional_extras"] else "Optional extras: <none>")
    print("uv sources: " + ", ".join(summary["uv_sources"]) if summary["uv_sources"] else "uv sources: <none>")
    print(f"Ruff configured: {summary['ruff_configured']}")
    print(f"Mypy configured: {summary['mypy_configured']}")
    print(f"Pytest configured: {summary['pytest_configured']}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Inspect a LangChain package pyproject without importing code."
    )
    parser.add_argument(
        "package_dir",
        type=Path,
        help="Path to a LangChain package directory containing pyproject.toml.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON instead of a text summary.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the metadata inspector."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    package_dir = args.package_dir.expanduser().resolve()

    try:
        data = load_pyproject(package_dir)
    except FileNotFoundError:
        print(f"Error: no pyproject.toml found in {package_dir}", file=sys.stderr)
        return 2
    except tomllib.TOMLDecodeError as error:
        print(f"Error: invalid pyproject.toml in {package_dir}: {error}", file=sys.stderr)
        return 2

    summary = summarize_package(package_dir, data)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_text_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
