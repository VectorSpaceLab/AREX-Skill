#!/usr/bin/env python3
"""List LlamaIndex monorepo packages from pyproject.toml files.

This script is read-only. It scans a supplied repository root, extracts package
metadata from pyproject.toml files, and prints a table or JSON for inspection.
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class PackageInfo:
    path: str
    name: str
    version: str | None
    requires_python: str | None
    import_path: str | None
    has_tests: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read LlamaIndex package metadata from pyproject.toml files."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root to scan. Defaults to the current directory.",
    )
    parser.add_argument(
        "--package-path",
        action="append",
        default=[],
        help="Repo-relative package path to inspect. May be passed multiple times.",
    )
    parser.add_argument(
        "--filter",
        default="",
        help="Case-insensitive substring matched against package name, path, or import path.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a text table.",
    )
    return parser.parse_args()


def load_package(pyproject_path: Path, repo_root: Path) -> PackageInfo | None:
    try:
        with pyproject_path.open("rb") as file_obj:
            data = tomllib.load(file_obj)
    except tomllib.TOMLDecodeError as exc:
        raise SystemExit(f"Could not parse {pyproject_path}: {exc}") from exc

    project = data.get("project")
    if not isinstance(project, dict) or not project.get("name"):
        return None

    package_dir = pyproject_path.parent
    llamahub = data.get("tool", {}).get("llamahub", {})
    import_path = llamahub.get("import_path") if isinstance(llamahub, dict) else None

    return PackageInfo(
        path=package_dir.relative_to(repo_root).as_posix() or ".",
        name=str(project["name"]),
        version=project.get("version"),
        requires_python=project.get("requires-python"),
        import_path=import_path,
        has_tests=(package_dir / "tests").is_dir(),
    )


def iter_pyprojects(repo_root: Path, package_paths: Iterable[str]) -> Iterable[Path]:
    requested = list(package_paths)
    if requested:
        for package_path in requested:
            pyproject_path = repo_root / package_path / "pyproject.toml"
            if not pyproject_path.is_file():
                raise SystemExit(f"No pyproject.toml found for package path: {package_path}")
            yield pyproject_path
        return

    skip_parts = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build"}
    for pyproject_path in repo_root.rglob("pyproject.toml"):
        if skip_parts.intersection(pyproject_path.relative_to(repo_root).parts):
            continue
        yield pyproject_path


def matches_filter(package: PackageInfo, query: str) -> bool:
    if not query:
        return True
    haystack = " ".join(
        value or ""
        for value in (package.path, package.name, package.requires_python, package.import_path)
    ).lower()
    return query.lower() in haystack


def print_table(packages: list[PackageInfo]) -> None:
    columns = ["path", "name", "version", "python", "tests", "import_path"]
    rows = [
        [
            package.path,
            package.name,
            package.version or "",
            package.requires_python or "",
            "yes" if package.has_tests else "no",
            package.import_path or "",
        ]
        for package in packages
    ]
    widths = [len(column) for column in columns]
    for row in rows:
        widths = [max(width, len(cell)) for width, cell in zip(widths, row)]

    print("  ".join(column.ljust(width) for column, width in zip(columns, widths)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(cell.ljust(width) for cell, width in zip(row, widths)))


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not repo_root.is_dir():
        print(f"Repository root does not exist: {repo_root}", file=sys.stderr)
        return 2

    packages = []
    for pyproject_path in iter_pyprojects(repo_root, args.package_path):
        package = load_package(pyproject_path, repo_root)
        if package and matches_filter(package, args.filter):
            packages.append(package)

    packages.sort(key=lambda package: package.path)
    if args.json:
        print(json.dumps([asdict(package) for package in packages], indent=2, sort_keys=True))
    else:
        print_table(packages)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
