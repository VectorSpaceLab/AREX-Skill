#!/usr/bin/env python3
"""Read-only layout checker for a LangChain partner package."""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path
from typing import Any


def _load_project(pyproject_path: Path) -> dict[str, Any]:
    with pyproject_path.open("rb") as file:
        data = tomllib.load(file)
    project = data.get("project")
    if not isinstance(project, dict):
        msg = f"missing [project] table in {pyproject_path}"
        raise ValueError(msg)
    return project


def _find_source_roots(package_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in package_dir.iterdir()
        if path.is_dir() and path.name.startswith("langchain_")
    )


def _relative(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def check_partner_package(package_dir: Path) -> int:
    """Print package layout facts and return a process status code."""
    package_dir = package_dir.resolve()
    failures: list[str] = []

    pyproject_path = package_dir / "pyproject.toml"
    if not pyproject_path.is_file():
        print(f"FAIL missing pyproject.toml: {package_dir}")
        return 1

    try:
        project = _load_project(pyproject_path)
    except (tomllib.TOMLDecodeError, ValueError) as exc:
        print(f"FAIL invalid pyproject.toml: {exc}")
        return 1

    name = project.get("name", "<missing>")
    version = project.get("version", "<missing>")
    python_range = project.get("requires-python", "<missing>")
    dependencies = project.get("dependencies", [])

    if not isinstance(dependencies, list):
        failures.append("[project].dependencies is not a list")
        dependencies = []

    source_roots = _find_source_roots(package_dir)
    if not source_roots:
        failures.append("no langchain_* source root found")

    print(f"package_dir: {package_dir}")
    print(f"distribution: {name}")
    print(f"version: {version}")
    print(f"requires_python: {python_range}")
    print("source_roots:")
    for root in source_roots:
        init_file = root / "__init__.py"
        status = "ok" if init_file.is_file() else "missing __init__.py"
        print(f"  - {_relative(root, package_dir)} ({status})")
        if not init_file.is_file():
            failures.append(f"{_relative(init_file, package_dir)} is missing")

    print("dependencies:")
    for dependency in dependencies:
        print(f"  - {dependency}")

    expected_paths = [
        Path("tests/unit_tests"),
        Path("tests/integration_tests"),
        Path("scripts/check_imports.py"),
        Path("scripts/check_version.py"),
    ]
    print("layout_checks:")
    for relative_path in expected_paths:
        path = package_dir / relative_path
        status = "ok" if path.exists() else "missing"
        print(f"  - {relative_path.as_posix()}: {status}")
        if not path.exists():
            failures.append(f"{relative_path.as_posix()} is missing")

    data_dirs = sorted(root / "data" for root in source_roots if (root / "data").is_dir())
    if data_dirs:
        print("profile_data_dirs:")
        for data_dir in data_dirs:
            profiles = data_dir / "_profiles.py"
            augmentations = data_dir / "profile_augmentations.toml"
            parts = ["_profiles.py" if profiles.is_file() else "missing _profiles.py"]
            if augmentations.is_file():
                parts.append("profile_augmentations.toml")
            print(f"  - {_relative(data_dir, package_dir)} ({', '.join(parts)})")
            if not profiles.is_file():
                failures.append(f"{_relative(profiles, package_dir)} is missing")

    if failures:
        print("FAILURES:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("OK partner_package_check")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check a LangChain partner package layout without imports or network calls."
    )
    parser.add_argument(
        "package_dir",
        type=Path,
        help="Path to libs/partners/<provider> package directory.",
    )
    args = parser.parse_args()
    return check_partner_package(args.package_dir)


if __name__ == "__main__":
    sys.exit(main())
