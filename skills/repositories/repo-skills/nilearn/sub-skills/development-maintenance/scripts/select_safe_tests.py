#!/usr/bin/env python3
"""Suggest targeted Nilearn validation commands for changed paths.

The script is intentionally no-network and read-only. It never runs tests.
Pass paths as arguments or pipe newline-separated paths on stdin.
"""

from __future__ import annotations

import argparse
import sys
from collections import OrderedDict
from pathlib import PurePosixPath


PLOTTING_PACKAGES = {"plotting", "reporting"}
ESTIMATOR_PACKAGES = {
    "connectome",
    "decoding",
    "decomposition",
    "glm",
    "maskers",
    "regions",
}
TOP_LEVEL_TESTS = {
    "masking.py": "nilearn/tests/test_masking.py",
    "signal.py": "nilearn/tests/test_signal.py",
}
SPECIAL_FILES = {
    "pyproject.toml": [
        "pre-commit run ruff-check --files pyproject.toml",
        "pre-commit run import-linter --files pyproject.toml",
    ],
    "tox.ini": [
        "tox list",
        "pre-commit run --files tox.ini",
    ],
    ".pre-commit-config.yaml": [
        "pre-commit run --files .pre-commit-config.yaml",
    ],
}


def normalize_path(path: str) -> str:
    """Return a stable relative POSIX path string."""
    cleaned = path.strip().replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned


def test_name_for_module(filename: str) -> str:
    """Map a source module filename to its conventional test filename."""
    stem = PurePosixPath(filename).stem
    if stem == "__init__":
        return "tests/"
    return f"tests/test_{stem}.py"


def tox_env_for_package(package: str | None) -> str:
    """Return the safest first-pass tox environment for a package."""
    if package in PLOTTING_PACKAGES:
        return "plotting"
    return "latest"


def command_for_test_path(test_path: str) -> str:
    """Suggest a tox command for a direct test path."""
    package = package_from_nilearn_path(test_path)
    env = tox_env_for_package(package)
    return f"tox -e {env} -- {test_path}"


def package_from_nilearn_path(path: str) -> str | None:
    """Return the first package segment under nilearn, if present."""
    parts = PurePosixPath(path).parts
    if len(parts) >= 2 and parts[0] == "nilearn":
        return parts[1]
    return None


def source_to_test_path(path: str) -> str | None:
    """Return a likely test path for a Nilearn source path."""
    parts = PurePosixPath(path).parts
    if not parts or parts[0] != "nilearn":
        return None
    if "tests" in parts:
        return path
    if len(parts) == 2 and parts[1] in TOP_LEVEL_TESTS:
        return TOP_LEVEL_TESTS[parts[1]]
    if not path.endswith(".py"):
        return None
    package = package_from_nilearn_path(path)
    if package is None:
        return None
    relative_file = PurePosixPath(*parts[2:]) if len(parts) > 2 else None
    if relative_file is None:
        return f"nilearn/{package}/tests/"
    if len(relative_file.parts) == 1:
        test_tail = test_name_for_module(relative_file.name)
        return f"nilearn/{package}/{test_tail}"
    parent = PurePosixPath(*relative_file.parts[:-1])
    test_tail = test_name_for_module(relative_file.name)
    if test_tail == "tests/":
        return f"nilearn/{package}/{parent}/tests/"
    return f"nilearn/{package}/{parent}/tests/{PurePosixPath(test_tail).name}"


def suggestions_for_path(path: str) -> list[str]:
    """Return suggested commands for one changed path."""
    normalized = normalize_path(path)
    if not normalized:
        return []

    commands = []
    if normalized in SPECIAL_FILES:
        commands.extend(SPECIAL_FILES[normalized])
    elif normalized.startswith("doc/"):
        commands.append(f"tox -e test_doc -- {normalized}")
        if normalized.endswith(".rst"):
            commands.append(f"pre-commit run doc8 --files {normalized}")
    elif normalized.startswith("examples/"):
        commands.append(
            "Run the changed example only if it is no-network and lightweight; "
            f"otherwise validate related unit tests for {normalized}."
        )
    elif normalized.startswith("maint_tools/"):
        commands.append(f"python {normalized} --help")
        commands.append(f"pre-commit run ruff-check --files {normalized}")
    elif normalized.startswith("build_tools/"):
        commands.append(f"python {normalized} --help")
        commands.append(f"pre-commit run ruff-check --files {normalized}")
    elif normalized.startswith("nilearn/"):
        test_path = source_to_test_path(normalized)
        if test_path:
            commands.append(command_for_test_path(test_path))
        package = package_from_nilearn_path(normalized)
        if package in ESTIMATOR_PACKAGES and "tests" not in normalized:
            commands.append(
                "Also run the package estimator/API compatibility test node "
                "if the change affects fit/transform, fitted attributes, "
                "or constructor parameters."
            )
        if package in PLOTTING_PACKAGES:
            commands.append(
                "Avoid pytest-mpl baseline comparisons unless pixel output "
                "intentionally changed."
            )
    else:
        commands.append(f"pre-commit run --files {normalized}")

    return commands


def read_paths(args_paths: list[str]) -> list[str]:
    """Read paths from CLI arguments or stdin."""
    if args_paths:
        return args_paths
    if sys.stdin.isatty():
        return []
    return [line.strip() for line in sys.stdin if line.strip()]


def unique_commands(paths: list[str]) -> OrderedDict[str, list[str]]:
    """Return path-to-command suggestions with duplicate commands removed."""
    result: OrderedDict[str, list[str]] = OrderedDict()
    for raw_path in paths:
        path = normalize_path(raw_path)
        if not path:
            continue
        seen = set()
        commands = []
        for command in suggestions_for_path(path):
            if command not in seen:
                seen.add(command)
                commands.append(command)
        result[path] = commands
    return result


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Suggest targeted Nilearn tox, pytest, or pre-commit commands "
            "for changed paths. Suggestions are printed only; nothing runs."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Changed paths, relative to the repository root. Reads stdin if omitted.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = read_paths(args.paths)
    if not paths:
        parser.print_help(sys.stderr)
        return 2

    suggestions = unique_commands(paths)
    for path, commands in suggestions.items():
        print(path)
        if not commands:
            print("  - No targeted suggestion available.")
            continue
        for command in commands:
            print(f"  - {command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
