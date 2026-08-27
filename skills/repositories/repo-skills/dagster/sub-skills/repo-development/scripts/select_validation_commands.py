#!/usr/bin/env python3
"""Suggest Dagster repo validation commands for changed paths.

This helper is intentionally read-only: it prints suggested commands and never
executes them. Pass one or more repository-relative changed paths as arguments.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable

Suggestion = tuple[str, str]
CommandPlan = tuple[tuple[Suggestion, ...], tuple[str, ...]]


def _norm(path: str) -> str:
    return path.strip().replace("\\", "/").lstrip("./")


def _add_command(commands: list[Suggestion], command: str, reason: str) -> None:
    if not any(item[0] == command for item in commands):
        commands.append((command, reason))


def _add_note(notes: list[str], note: str) -> None:
    if note not in notes:
        notes.append(note)


def build_plan(paths: Iterable[str]) -> CommandPlan:
    normalized = [_norm(path) for path in paths if _norm(path)]
    commands: list[Suggestion] = []
    notes: list[str] = []

    has_python = any(path.endswith((".py", ".pyi", ".ipynb")) for path in normalized)
    has_docs = any(
        path.startswith("docs/") or path.startswith("examples/docs_snippets/")
        for path in normalized
    )
    has_docs_api = any(path.startswith("docs/") and path.endswith(".rst") for path in normalized)
    has_ui = any(path.startswith("js_modules/") for path in normalized)
    has_ui_components = any(path.startswith("js_modules/ui-components/") for path in normalized)
    has_graphql = any(
        path.startswith("python_modules/dagster-graphql/")
        or "graphql" in path.lower()
        or path.endswith(("schema.graphql", ".graphql"))
        for path in normalized
    )
    has_package_metadata = any(
        path.endswith("setup.py")
        or path.endswith("pyproject.toml")
        or path.endswith("setup.cfg")
        for path in normalized
    )

    if has_python:
        _add_command(commands, "make ruff", "Mandatory after every Python file edit.")

    for path in normalized:
        if path.startswith("python_modules/dagster/dagster_tests/"):
            _add_command(commands, f"pytest {path}", "Focused core Dagster test file or directory.")
        elif path.startswith("python_modules/dagster/dagster/"):
            _add_command(
                commands,
                "pytest python_modules/dagster/dagster_tests/<focused_test_path>",
                "Core Dagster code changed; choose the nearest focused test.",
            )
        elif path.startswith("python_modules/dagster-graphql/"):
            _add_command(
                commands,
                "pytest python_modules/dagster-graphql/dagster_graphql_tests/<focused_test_path>",
                "GraphQL package changed; choose the nearest focused test.",
            )
        elif path.startswith("python_modules/dagster-webserver/"):
            _add_command(
                commands,
                "pytest python_modules/dagster-webserver/dagster_webserver_tests/<focused_test_path>",
                "Webserver package changed; choose the nearest focused test.",
            )
        elif path.startswith("python_modules/dagster-pipes/"):
            _add_command(
                commands,
                "pytest python_modules/dagster-pipes/dagster_pipes_tests/<focused_test_path>",
                "Pipes package changed; choose the nearest focused test.",
            )
        elif path.startswith("python_modules/libraries/dagster-shared/"):
            _add_command(
                commands,
                "pytest python_modules/libraries/dagster-shared/dagster_shared_tests/<focused_test_path>",
                "Shared utilities changed; choose the nearest focused test.",
            )
        elif path.startswith("python_modules/libraries/") and path.endswith((".py", ".pyi")):
            _add_command(
                commands,
                "pytest python_modules/libraries/<package>/<package_tests>/<focused_test_path>",
                "Integration-library Python changed; choose package-local tests.",
            )

    if has_python and not any(command.startswith("pytest ") for command, _reason in commands):
        _add_command(
            commands,
            "pytest <focused_test_path>",
            "Python changed; run the nearest focused pytest path.",
        )

    if has_package_metadata:
        _add_command(
            commands,
            "uv pip install -e .",
            "Package metadata or entry points changed; reinstall from the affected package root.",
        )
        _add_note(notes, "Run editable reinstall from the package directory that owns the changed metadata.")

    if has_graphql:
        _add_command(
            commands,
            "cd js_modules && make generate-graphql",
            "GraphQL schema or GraphQL-facing backend changed; regenerate UI types first.",
        )

    if has_ui or has_graphql:
        _add_command(commands, "cd js_modules && yarn tsgo", "Type-check UI workspaces.")
        _add_command(commands, "cd js_modules && yarn lint", "Lint UI workspaces.")
        _add_command(commands, "cd js_modules && yarn jest", "Run UI Jest tests after UI edits.")

    if has_ui_components:
        _add_command(commands, "cd js_modules && yarn build", "Verify ui-components production build.")

    if has_docs:
        _add_command(commands, "cd docs && yarn build", "Validate docs site after docs edits.")

    if has_docs_api:
        _add_command(
            commands,
            "cd docs && yarn build-api-docs",
            "Validate generated API docs after .rst edits.",
        )

    if not commands:
        _add_note(
            notes,
            "No specific command matched. Inspect changed paths and choose the nearest focused validation.",
        )

    if any(".tox/" in path or path.startswith(".tox/") for path in normalized):
        _add_note(notes, "Avoid using .tox paths for source lookup; they are temporary environments.")

    return (tuple(commands), tuple(notes))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Suggest Dagster repo validation commands for changed paths without running them.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Repository-relative changed paths, e.g. python_modules/dagster/dagster/_core/foo.py",
    )
    args = parser.parse_args()

    commands, notes = build_plan(args.paths)
    if commands:
        print("Suggested commands:")
        for command, reason in commands:
            print(f"- {command}")
            print(f"  reason: {reason}")
    if notes:
        print("Notes:")
        for note in notes:
            print(f"- {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
