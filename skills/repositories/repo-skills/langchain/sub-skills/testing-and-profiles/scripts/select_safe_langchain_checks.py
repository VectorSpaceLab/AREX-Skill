#!/usr/bin/env python3
"""Print safe LangChain package verification commands.

This script is read-only. It inspects a package-local pyproject.toml and nearby
files, then recommends deterministic checks while flagging integration risks.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - compatibility path for Python 3.10 users
    import tomli as tomllib  # type: ignore[import-not-found]


RISKY_NAMES = (
    "integration_tests",
    "mock_servers",
    "cassettes",
    "cassette",
    "recording",
)


def _load_pyproject(package_dir: Path) -> dict[str, object]:
    pyproject_path = package_dir / "pyproject.toml"
    if not pyproject_path.exists():
        msg = f"No pyproject.toml found at {pyproject_path}"
        raise SystemExit(msg)
    with pyproject_path.open("rb") as file:
        return tomllib.load(file)


def _dependency_groups(config: dict[str, object]) -> dict[str, list[str]]:
    groups = config.get("dependency-groups", {})
    if not isinstance(groups, dict):
        return {}
    normalized: dict[str, list[str]] = {}
    for name, values in groups.items():
        if isinstance(name, str) and isinstance(values, list):
            normalized[name] = [str(value) for value in values]
    return normalized


def _project_name(config: dict[str, object]) -> str:
    project = config.get("project", {})
    if isinstance(project, dict) and isinstance(project.get("name"), str):
        return str(project["name"])
    return "unknown-package"


def _pytest_markers(config: dict[str, object]) -> list[str]:
    tool = config.get("tool", {})
    if not isinstance(tool, dict):
        return []
    pytest_options = tool.get("pytest", {})
    if not isinstance(pytest_options, dict):
        return []
    ini_options = pytest_options.get("ini_options", {})
    if not isinstance(ini_options, dict):
        return []
    markers = ini_options.get("markers", [])
    return [str(marker).split(":", 1)[0] for marker in markers if isinstance(marker, str)]


def _dependency_name(dependency: str) -> str:
    match = re.match(r"[A-Za-z0-9_.-]+", dependency)
    return match.group(0).lower() if match else dependency.lower()


def _has_dependency(groups: dict[str, list[str]], group: str, package: str) -> bool:
    return any(_dependency_name(dep) == package for dep in groups.get(group, []))


def _existing_paths(package_dir: Path, paths: list[str]) -> list[str]:
    return [path for path in paths if (package_dir / path).exists()]


def _unit_test_targets(package_dir: Path, changed_paths: list[str]) -> list[str]:
    explicit_tests = [path for path in changed_paths if "tests/unit_tests" in path and path.endswith(".py")]
    if explicit_tests:
        return explicit_tests
    defaults = _existing_paths(
        package_dir,
        [
            "tests/unit_tests",
            "tests/unit_tests/test_standard.py",
            "tests/unit_tests/test_cli.py",
        ],
    )
    if "tests/unit_tests" in defaults:
        return ["tests/unit_tests"]
    return defaults[:1]


def _changed_paths_from_args(values: list[str]) -> list[str]:
    return [value.replace("\\", "/") for value in values]


def _print_commands(package_dir: Path, changed_paths: list[str]) -> int:
    config = _load_pyproject(package_dir)
    groups = _dependency_groups(config)
    project_name = _project_name(config)
    markers = _pytest_markers(config)
    makefile_exists = (package_dir / "Makefile").exists()
    scripts_dir = package_dir / "scripts"
    unit_targets = _unit_test_targets(package_dir, changed_paths)

    print(f"Package: {project_name}")
    print(f"Directory: {package_dir}")
    print(f"Dependency groups: {', '.join(sorted(groups)) or 'none declared'}")
    print(f"Pytest markers: {', '.join(markers) or 'none declared'}")
    print()

    print("Safe setup:")
    if "test" in groups:
        print("  uv sync --group test")
    else:
        print("  # No test dependency group found; inspect package metadata before running pytest.")
    print()

    print("Safe deterministic checks:")
    if unit_targets and "test" in groups:
        for target in unit_targets:
            print(f"  uv run --group test pytest {target}")
    elif "test" in groups:
        print("  uv run --group test pytest tests/unit_tests")
    else:
        print("  # No safe pytest command inferred.")

    if "lint" in groups:
        print("  uv run --group lint ruff check .")
    if "typing" in groups:
        print("  uv run --group typing mypy .")

    if makefile_exists:
        print("  # Package has a Makefile; prefer its scoped targets when they match the task.")

    check_imports = scripts_dir / "check_imports.py"
    lint_imports = scripts_dir / "lint_imports.sh"
    check_version = scripts_dir / "check_version.py"
    if check_imports.exists():
        print("  uv run --group test python scripts/check_imports.py <changed-python-files>")
    if lint_imports.exists():
        print("  bash scripts/lint_imports.sh")
    if check_version.exists():
        print("  uv run --group test python scripts/check_version.py")
    print()

    print("Skip or ask before running:")
    risky_paths = [path for path in changed_paths if any(name in path for name in RISKY_NAMES)]
    if risky_paths:
        print("  - Changed paths include integration/service/cassette-related files.")
    if "test_integration" in groups:
        print("  - Integration tests: require explicit approval plus credentials/services when applicable.")
    if _has_dependency(groups, "test", "pytest-socket"):
        print("  - Network/socket tests: pytest-socket is present; do not enable network by default.")
    if _has_dependency(groups, "test", "syrupy"):
        print("  - Snapshot updates: run only after intentional output-change confirmation.")
    if _has_dependency(groups, "test", "pytest-recording") or _has_dependency(groups, "test", "vcrpy"):
        print("  - Cassette recording: do not re-record without network and credential approval.")
    if "scheduled" in markers:
        print("  - Scheduled tests: exclude from local default verification unless requested.")
    if not any(
        [
            risky_paths,
            "test_integration" in groups,
            _has_dependency(groups, "test", "pytest-socket"),
            _has_dependency(groups, "test", "syrupy"),
            _has_dependency(groups, "test", "pytest-recording"),
            _has_dependency(groups, "test", "vcrpy"),
            "scheduled" in markers,
        ]
    ):
        print("  - No high-risk test features detected from package metadata.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "package_dir",
        type=Path,
        help="Path to a LangChain package directory such as libs/core or libs/text-splitters.",
    )
    parser.add_argument(
        "changed_paths",
        nargs="*",
        help="Optional changed paths, relative to the package directory.",
    )
    args = parser.parse_args()
    package_dir = args.package_dir.resolve()
    changed_paths = _changed_paths_from_args(args.changed_paths)
    return _print_commands(package_dir, changed_paths)


if __name__ == "__main__":
    raise SystemExit(main())
