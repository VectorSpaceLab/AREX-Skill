#!/usr/bin/env python3
"""List OpenLLMetry package metadata from a checkout.

The script is intentionally read-only and does not import project packages,
install dependencies, touch lock files, or access the network.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - only used on Python 3.10
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise SystemExit("Python 3.11+ or the tomli package is required") from exc


def _load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _sorted_mapping(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sorted_mapping(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_sorted_mapping(item) for item in value]
    return value


def _normalise_uv_sources(raw_sources: dict[str, Any]) -> dict[str, Any]:
    normalised: dict[str, Any] = {}
    for name in sorted(raw_sources):
        value = raw_sources[name]
        if isinstance(value, dict):
            normalised[name] = {
                key: value[key]
                for key in sorted(value)
                if key in {"path", "editable", "workspace", "index", "url"}
            }
        else:
            normalised[name] = value
    return normalised


def _package_record(package_root: Path, repo_root: Path) -> dict[str, Any]:
    pyproject = _load_toml(package_root / "pyproject.toml")
    project_json = _load_json(package_root / "project.json")

    project = pyproject.get("project", {})
    tool_uv = pyproject.get("tool", {}).get("uv", {})

    tests_root = package_root / "tests"
    test_files = []
    cassette_dirs = []
    if tests_root.exists():
        test_files = sorted(
            _rel(path, repo_root)
            for path in tests_root.glob("**/*.py")
            if path.is_file() and path.name.startswith("test")
        )
        cassette_dirs = sorted(
            _rel(path, repo_root)
            for path in tests_root.glob("**/cassettes")
            if path.is_dir()
        )

    return {
        "directory": _rel(package_root, repo_root),
        "name": project.get("name"),
        "version": project.get("version"),
        "description": project.get("description"),
        "requires_python": project.get("requires-python"),
        "project_type": project_json.get("projectType"),
        "source_root": project_json.get("sourceRoot"),
        "tags": sorted(project_json.get("tags", [])),
        "targets": sorted(project_json.get("targets", {}).keys()),
        "entry_points": _sorted_mapping(project.get("entry-points", {})),
        "optional_dependencies": sorted(project.get("optional-dependencies", {}).keys()),
        "dependency_groups": sorted(pyproject.get("dependency-groups", {}).keys()),
        "uv_sources": _normalise_uv_sources(tool_uv.get("sources", {})),
        "tests": test_files,
        "cassette_dirs": cassette_dirs,
    }


def collect_projects(repo_root: Path) -> dict[str, Any]:
    packages_dir = repo_root / "packages"
    package_roots = sorted(path.parent for path in packages_dir.glob("*/pyproject.toml"))
    packages = [_package_record(package_root, repo_root) for package_root in package_roots]

    return {
        "summary": {
            "package_count": len(packages),
            "packages_with_entry_points": sum(1 for item in packages if item["entry_points"]),
            "packages_with_tests": sum(1 for item in packages if item["tests"]),
        },
        "packages": packages,
    }


def print_text(data: dict[str, Any]) -> None:
    summary = data["summary"]
    print(
        "OpenLLMetry projects: "
        f"{summary['package_count']} packages, "
        f"{summary['packages_with_entry_points']} with entry points, "
        f"{summary['packages_with_tests']} with tests"
    )
    for package in data["packages"]:
        print()
        print(f"{package['name']} ({package['directory']})")
        print(f"  version: {package['version']}")
        print(f"  python: {package['requires_python']}")
        print(f"  project type: {package['project_type']}")
        print(f"  source root: {package['source_root']}")
        print(f"  targets: {', '.join(package['targets']) or '-'}")
        print(f"  tests: {len(package['tests'])}")
        if package["cassette_dirs"]:
            print(f"  cassette dirs: {', '.join(package['cassette_dirs'])}")
        if package["entry_points"]:
            print("  entry points:")
            for group, entries in package["entry_points"].items():
                print(f"    [{group}]")
                for name, target in entries.items():
                    print(f"      {name} = {target}")
        if package["uv_sources"]:
            print("  uv sources:")
            for name, value in package["uv_sources"].items():
                print(f"    {name}: {value}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List OpenLLMetry package metadata, source roots, tests, entry points, and local uv sources.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        type=Path,
        help="Path to the OpenLLMetry checkout root.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    repo_root = args.repo_root.resolve()
    if not (repo_root / "package.json").exists() or not (repo_root / "packages").is_dir():
        print("error: --repo-root must point to an OpenLLMetry checkout root", file=sys.stderr)
        return 2

    data = collect_projects(repo_root)
    if args.format == "text":
        print_text(data)
    else:
        json.dump(data, sys.stdout, indent=2, sort_keys=True)
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
