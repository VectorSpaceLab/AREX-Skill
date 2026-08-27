#!/usr/bin/env python3
"""Suggest focused Hatch validation commands for common Haystack repo paths.

The script is deterministic and side-effect free. Pass changed file paths; it prints
conservative commands that a contributor can choose from.
"""

from __future__ import annotations

import argparse
from pathlib import PurePosixPath


COMPONENT_GROUPS = {
    "agents",
    "audio",
    "builders",
    "caching",
    "classifiers",
    "connectors",
    "converters",
    "embedders",
    "evaluators",
    "extractors",
    "fetchers",
    "generators",
    "joiners",
    "preprocessors",
    "query",
    "rankers",
    "readers",
    "retrievers",
    "routers",
    "samplers",
    "tools",
    "validators",
    "websearch",
    "writers",
}

CORE_AREAS = {
    "component": "test/core/component",
    "pipeline": "test/core/pipeline",
    "super_component": "test/core/super_component",
}

TOP_LEVEL_TEST_AREAS = {
    "dataclasses": "test/dataclasses",
    "document_stores": "test/document_stores",
    "evaluation": "test/evaluation",
    "human_in_the_loop": "test/human_in_the_loop",
    "marshal": "test/marshal",
    "testing": "test/testing",
    "tools": "test/tools",
    "tracing": "test/tracing",
    "utils": "test/utils",
}


def normalize(path: str) -> PurePosixPath:
    """Return a normalized POSIX-style path without requiring it to exist."""
    return PurePosixPath(path.replace("\\", "/").strip("/"))


def add_command(commands: list[str], command: str) -> None:
    """Append command if it has not already been suggested."""
    if command not in commands:
        commands.append(command)


def suggest_for_path(path: PurePosixPath, commands: list[str]) -> None:
    """Add focused validation commands for one changed path."""
    parts = path.parts
    path_text = path.as_posix()

    if not parts:
        return

    if parts[0] == "test":
        add_command(commands, f"hatch run test:unit {path_text}")
        return

    if parts[0] == "haystack" and len(parts) >= 3 and parts[1] == "components":
        group = parts[2]
        if group in COMPONENT_GROUPS:
            add_command(commands, f"hatch run test:unit test/components/{group}")
        else:
            add_command(commands, "hatch run test:unit test/components")
        return

    if parts[0] == "haystack" and len(parts) >= 3 and parts[1] == "core":
        area = parts[2]
        add_command(commands, f"hatch run test:unit {CORE_AREAS.get(area, 'test/core')}")
        return

    if parts[0] == "haystack" and len(parts) >= 2:
        area = parts[1]
        test_area = TOP_LEVEL_TEST_AREAS.get(area)
        if test_area:
            add_command(commands, f"hatch run test:unit {test_area}")
        else:
            add_command(commands, "hatch run test:unit test")
        return

    if parts[0] == "scripts":
        add_command(commands, f"hatch -e test run python {path_text} --help")
        if path.name == "release_note_backticks.py":
            add_command(commands, "hatch run test:unit test/test_release_note_backticks.py")
        return

    if parts[0] == "releasenotes":
        add_command(commands, f"hatch -e test run python scripts/release_note_backticks.py --check {path_text}")
        return

    if parts[0] == "docs-website":
        add_command(commands, "cd docs-website && npm run build")
        return

    if path.name in {"pyproject.toml", "VERSION.txt"}:
        add_command(commands, "hatch --version")
        add_command(commands, "hatch run fmt-check")
        return

    if path.suffix == ".md":
        add_command(commands, "hatch run fmt-check")


def main() -> int:
    """Parse path arguments and print suggested commands."""
    parser = argparse.ArgumentParser(description="Suggest focused Haystack Hatch checks for changed paths.")
    parser.add_argument("paths", nargs="+", help="Changed repository paths, such as haystack/core/pipeline/pipeline.py")
    args = parser.parse_args()

    commands: list[str] = []
    for raw_path in args.paths:
        suggest_for_path(normalize(raw_path), commands)

    if not commands:
        print("No focused command matched. Start with: hatch run test:unit test")
        print("Then consider: hatch run fmt-check")
        return 0

    print("Suggested focused checks:")
    for command in commands:
        print(f"- {command}")

    print("Optional broader checks:")
    print("- hatch run fmt")
    print("- hatch run test:types")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
