#!/usr/bin/env python3
"""Suggest focused Prefect validation commands for changed paths.

This helper is intentionally read-only. It does not inspect git state, run tests,
start services, or modify files; it only maps paths supplied on the command line
to conservative validation suggestions.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Iterable


@dataclass(frozen=True)
class Suggestion:
    reason: str
    commands: tuple[str, ...]
    notes: tuple[str, ...] = ()


@dataclass
class Result:
    paths: list[str] = field(default_factory=list)
    suggestions: dict[str, Suggestion] = field(default_factory=dict)
    warnings: set[str] = field(default_factory=set)

    def add(self, key: str, suggestion: Suggestion) -> None:
        self.suggestions.setdefault(key, suggestion)

    def warn(self, warning: str) -> None:
        self.warnings.add(warning)


def normalize_path(path: str) -> str:
    value = path.strip().replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return str(PurePosixPath(value)) if value else value


def command_for_files(files: Iterable[str]) -> tuple[str, ...]:
    selected = [path for path in files if path.endswith((".py", ".pyi"))]
    if not selected:
        return ()
    joined = " ".join(selected)
    return (
        f"uv run ruff check --fix {joined}",
        f"uv run ruff format {joined}",
        f"uv run pre-commit run --files {joined}",
    )


def categorize(path: str, result: Result) -> None:
    py_files = [path] if path.endswith((".py", ".pyi")) else []

    if path == "pyproject.toml":
        result.add(
            "root-dependencies",
            Suggestion(
                "Root package metadata or dependencies changed.",
                (
                    "uv lock",
                    "uv run pytest tests/test_import_smoke.py -x --tb=short",
                    "uv run pre-commit run --files pyproject.toml uv.lock",
                ),
                (
                    "If the dependency is client-visible, mirror it in client/pyproject.toml.",
                    "Do not use pip install or uv pip for repository dependency management.",
                ),
            ),
        )
        return

    if path == "uv.lock":
        result.add(
            "uv-lock",
            Suggestion(
                "Dependency lockfile changed.",
                ("uv run pre-commit run uv-lock",),
                ("Pair lockfile changes with the pyproject metadata that caused them.",),
            ),
        )
        return

    if path.startswith("client/"):
        result.add(
            "prefect-client-package",
            Suggestion(
                "The separate prefect-client package build may be affected.",
                (
                    "uv run pytest tests/client/ -x --tb=short",
                    "bash client/build_client.sh",
                ),
                (
                    "Mirror client-visible root dependency changes in client/pyproject.toml.",
                    "Keep server-only and CLI imports out of code shipped in prefect-client.",
                ),
            ),
        )
        return

    if path.startswith("src/prefect/client/"):
        result.add(
            "client-sdk",
            Suggestion(
                "Client SDK code changed.",
                (
                    "uv run pytest tests/client/ -x --tb=short",
                    "bash client/build_client.sh",
                )
                + command_for_files(py_files),
                (
                    "Check both sync and async client variants where applicable.",
                    "Avoid imports that reach server/database or server/models.",
                ),
            ),
        )
        return

    if path.startswith("src/prefect/server/database/"):
        result.add(
            "server-database",
            Suggestion(
                "Server database or migration code changed.",
                (
                    "uv run pytest tests/server/database/ -x --tb=short",
                    "uv run pytest tests/server/ -k affected_resource -x --tb=short",
                )
                + command_for_files(py_files),
                ("Validate both SQLite and PostgreSQL behavior before finalizing broad database changes.",),
            ),
        )
        result.warn("PostgreSQL validation requires a running service or CI-equivalent environment.")
        return

    if path.startswith("src/prefect/server/orchestration/"):
        result.add(
            "server-orchestration",
            Suggestion(
                "Server orchestration policy or state-transition code changed.",
                (
                    "uv run pytest tests/server/orchestration/ -x --tb=short",
                    "uv run pytest tests/server/orchestration/api/ -x --tb=short",
                )
                + command_for_files(py_files),
                (
                    "Do not bypass orchestration state transitions, even in tests.",
                    "Remember force=True still routes through MinimalFlowPolicy.",
                ),
            ),
        )
        return

    if path.startswith("src/prefect/server/api/"):
        result.add(
            "server-api",
            Suggestion(
                "Server API route code changed.",
                (
                    "uv run pytest tests/server/api/ -x --tb=short",
                    "just generate-openapi",
                )
                + command_for_files(py_files),
                ("Consider UI-v2 service sync if response schemas affect the frontend.",),
            ),
        )
        return

    if path.startswith("src/prefect/server/"):
        result.add(
            "server-core",
            Suggestion(
                "Server backend code changed.",
                ("uv run pytest tests/server/ -k affected_resource -x --tb=short",)
                + command_for_files(py_files),
                (
                    "Keep server/client schemas separate.",
                    "Database-related changes must account for SQLite and PostgreSQL.",
                ),
            ),
        )
        return

    if path.startswith("src/prefect/cli/"):
        result.add(
            "cli",
            Suggestion(
                "CLI command code changed.",
                (
                    "uv run pytest tests/cli/ -k affected_command -x --tb=short",
                    "just generate-cli-docs",
                )
                + command_for_files(py_files),
                (
                    "Use rich output and exit_with_error for error exits.",
                    "Keep --json output free of human-readable diagnostics.",
                ),
            ),
        )
        return

    if path.startswith("src/prefect/settings/"):
        result.add(
            "settings",
            Suggestion(
                "Settings code changed.",
                (
                    "uv run pytest tests/test_settings.py -x --tb=short",
                    "just generate-settings",
                    "uv run pre-commit run generate-settings-types --all-files",
                )
                + command_for_files(py_files),
                ("Update SUPPORTED_SETTINGS in tests/test_settings.py for new settings.",),
            ),
        )
        return

    if path.startswith("src/prefect/events/"):
        result.add(
            "events-client",
            Suggestion(
                "Client-side events code changed.",
                ("uv run pytest tests/events/ -x --tb=short",) + command_for_files(py_files),
                (
                    "Client and server event schemas are separate but structurally mirrored.",
                    "Checkpointing has count-based and time-based paths.",
                ),
            ),
        )
        return

    if path.startswith("src/prefect/deployments/"):
        result.add(
            "deployments",
            Suggestion(
                "Deployment code or prefect.yaml behavior changed.",
                (
                    "uv run pytest tests/deployment/ -x --tb=short",
                    "uv run pytest tests/cli/deploy/ -x --tb=short",
                    "just generate-prefect-yaml-schema",
                )
                + command_for_files(py_files),
                ("Step requires can install packages at runtime; review side effects carefully.",),
            ),
        )
        return

    if path.startswith("src/prefect/runner/"):
        result.add(
            "runner",
            Suggestion(
                "Runner execution code changed.",
                ("uv run pytest tests/runner/ -x --tb=short",) + command_for_files(py_files),
                ("Route deployment command behavior to deployment and CLI tests too.",),
            ),
        )
        return

    if path.startswith("src/prefect/workers/"):
        result.add(
            "workers",
            Suggestion(
                "Worker code changed.",
                ("uv run pytest tests/workers/ -x --tb=short",) + command_for_files(py_files),
                ("Keep worker channel sync ownership at the channel boundary.",),
            ),
        )
        return

    for package, test_path in (
        ("blocks", "tests/blocks/"),
        ("assets", "tests/assets/"),
        ("concurrency", "tests/concurrency/"),
        ("results", "tests/results/"),
        ("logging", "tests/logging/"),
        ("utilities/schema_tools", "tests/utilities/schema_tools/"),
        ("utilities", "tests/utilities/"),
    ):
        if path.startswith(f"src/prefect/{package}/"):
            result.add(
                package.replace("/", "-"),
                Suggestion(
                    f"Prefect {package} code changed.",
                    (f"uv run pytest {test_path} -x --tb=short",) + command_for_files(py_files),
                    ("Search for cross-component users before broadening validation.",),
                ),
            )
            return

    if path in {"src/prefect/flow_engine.py", "src/prefect/task_engine.py"}:
        result.add(
            "execution-engines",
            Suggestion(
                "Flow or task engine code changed.",
                (
                    "uv run pytest tests/test_flow_engine.py tests/test_task_engine.py -x --tb=short",
                    "uv run pytest tests/engine/ -x --tb=short",
                )
                + command_for_files(py_files),
                ("Keep sync and async engine paths in lockstep.",),
            ),
        )
        return

    top_level_map = {
        "src/prefect/flows.py": ("flows", "uv run pytest tests/test_flows.py -x --tb=short"),
        "src/prefect/tasks.py": ("tasks", "uv run pytest tests/test_tasks.py -x --tb=short"),
        "src/prefect/states.py": ("states", "uv run pytest tests/test_states.py -x --tb=short"),
        "src/prefect/futures.py": ("futures", "uv run pytest tests/test_futures.py -x --tb=short"),
        "src/prefect/task_runners.py": ("task-runners", "uv run pytest tests/test_task_runners.py -x --tb=short"),
        "src/prefect/transactions.py": ("transactions", "uv run pytest tests/test_transactions.py -x --tb=short"),
        "src/prefect/cache_policies.py": ("cache-policies", "uv run pytest tests/test_cache_policies.py -x --tb=short"),
    }
    if path in top_level_map:
        key, command = top_level_map[path]
        result.add(
            key,
            Suggestion(
                f"Top-level {key} runtime code changed.",
                (command,) + command_for_files(py_files),
                ("Route user-facing API semantics to flow-task-authoring when writing public guidance.",),
            ),
        )
        return

    if path.startswith("src/prefect/"):
        module = path.removeprefix("src/prefect/").split("/", 1)[0]
        result.add(
            "prefect-source-generic",
            Suggestion(
                "Prefect source code changed but no narrower mapping matched.",
                (
                    f"rg -n \"{module}\" tests src/prefect",
                    "uv run pytest tests/ -k affected_symbol -x --tb=short",
                )
                + command_for_files(py_files),
                ("Prefer a narrower mirrored test path after searching for symbol usage.",),
            ),
        )
        return

    if path.startswith("tests/"):
        result.add(
            "tests-changed",
            Suggestion(
                "Tests changed.",
                (
                    f"uv run pytest {path if path.endswith('.py') else path.rstrip('/') + '/'} -x --tb=short",
                    "review the repository CI test-selection matrix for moved or new tests",
                )
                + command_for_files(py_files),
                ("Verify CI selection coverage if tests were added, moved, renamed, or excluded.",),
            ),
        )
        return

    if path.startswith("docs/"):
        result.add(
            "docs",
            Suggestion(
                "Documentation changed.",
                ("just links", "just lint"),
                (
                    "Do not hand-edit generated docs directories unless the scoped docs instructions allow it.",
                    "Register navigable pages in docs/docs.json.",
                ),
            ),
        )
        return

    if path.startswith("examples/"):
        result.add(
            "examples",
            Suggestion(
                "Example code changed and may feed generated docs.",
                (
                    f"uv run -s {path}" if path.endswith(".py") else "uv run pytest tests/ -k example -x --tb=short",
                    "just generate-examples",
                ),
                ("Avoid network, credentials, or long-lived services in examples unless clearly marked.",),
            ),
        )
        return

    if path.startswith("schemas/"):
        result.add(
            "schemas",
            Suggestion(
                "Repository JSON schemas changed.",
                (
                    "just generate-prefect-yaml-schema",
                    "uv run pytest tests/cli/deploy/test_prefect_yaml_schema.py -x --tb=short",
                ),
                ("Regenerate from source models instead of patching derived schema symptoms.",),
            ),
        )
        return

    if path.startswith("scripts/"):
        result.add(
            "scripts",
            Suggestion(
                "Repository utility or generation script changed.",
                (
                    f"uv run python {path} --help" if path.endswith(".py") else "uv run pre-commit run --files " + path,
                    "review the repository CI test-selection matrix for moved or new tests",
                )
                + command_for_files(py_files),
                ("Treat release, publishing, Postgres, and integration service scripts as opt-in only.",),
            ),
        )
        return

    if path.startswith("src/integrations/"):
        parts = path.split("/")
        integration_dir = "/".join(parts[:3]) if len(parts) >= 3 else "src/integrations/<package>"
        result.add(
            "integration-package",
            Suggestion(
                "An integration package changed.",
                (
                    f"uv run --project ./{integration_dir} pytest {integration_dir}/tests/ -x --tb=short",
                    f"just --justfile {integration_dir}/justfile --working-directory {integration_dir} api-ref",
                ),
                (
                    "Integrations are separately versioned packages; do not treat them as core modules.",
                    "Skip release-note generation unless the task explicitly asks for it.",
                ),
            ),
        )
        return

    if path.startswith("ui-v2/"):
        result.add(
            "ui-v2",
            Suggestion(
                "React UI-v2 code changed.",
                (
                    "cd ui-v2 && npm run check",
                    "cd ui-v2 && npm run lint",
                    "cd ui-v2 && npm test -- <focused-name>",
                ),
                (
                    "Use semantic color tokens and MSW mocks.",
                    "Run npm run service-sync when backend API types changed.",
                ),
            ),
        )
        return

    if path.startswith(("integration-tests/", "compat-tests/", "load_testing/", "benches/")):
        result.add(
            "expensive-suite",
            Suggestion(
                "A broad, service-heavy, compatibility, load, or benchmark suite changed.",
                ("uv run pytest <focused-path> -x --tb=short",),
                ("Confirm required services and expected runtime before running broad checks.",),
            ),
        )
        result.warn("This path may require long-running services, benchmarks, or external resources.")
        return

    result.add(
        "generic",
        Suggestion(
            "No specific mapping matched.",
            (
                f"uv run pre-commit run --files {path}",
                "rg -n \"affected_symbol\" tests src/prefect docs",
            ),
            ("Inspect nearby AGENTS.md files and choose the smallest meaningful validation.",),
        ),
    )


def build_result(paths: list[str]) -> Result:
    result = Result(paths=paths)
    if not paths:
        result.add(
            "no-paths",
            Suggestion(
                "No paths were provided.",
                (
                    "python sub-skills/repo-development/scripts/select_prefect_tests.py src/prefect/client/example.py tests/client/test_example.py",
                    "uv run pytest tests/path.py -k test_name -x --tb=short",
                ),
                ("Pass changed paths from a PR, issue investigation, or editor selection.",),
            ),
        )
        return result

    for path in paths:
        categorize(path, result)

    result.add(
        "always-consider",
        Suggestion(
            "General Prefect maintainer checks to consider after focused validation passes.",
            (
                "uv run ruff check --fix <changed-python-files>",
                "uv run ruff format <changed-python-files>",
                "uv run pre-commit run --files <changed-files>",
            ),
            (
                "Broaden to uv run pre-commit run --all-files only when hooks or broad generated artifacts are affected.",
                "Run full suites, Postgres, Docker, and integration checks only when the change requires them.",
            ),
        ),
    )
    return result


def as_json(result: Result) -> str:
    payload = {
        "paths": result.paths,
        "suggestions": {
            key: {
                "reason": suggestion.reason,
                "commands": list(suggestion.commands),
                "notes": list(suggestion.notes),
            }
            for key, suggestion in result.suggestions.items()
        },
        "warnings": sorted(result.warnings),
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def as_text(result: Result) -> str:
    lines: list[str] = []
    if result.paths:
        lines.append("Changed paths:")
        lines.extend(f"  - {path}" for path in result.paths)
        lines.append("")

    lines.append("Suggested validation:")
    for key, suggestion in result.suggestions.items():
        lines.append(f"\n[{key}] {suggestion.reason}")
        for command in suggestion.commands:
            lines.append(f"  $ {command}")
        for note in suggestion.notes:
            lines.append(f"  note: {note}")

    if result.warnings:
        lines.append("\nWarnings:")
        for warning in sorted(result.warnings):
            lines.append(f"  - {warning}")

    lines.append("\nThis helper only suggests commands; review scoped AGENTS.md rules before editing or running validation.")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Suggest focused Prefect repo validation commands for changed paths.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Changed files or directories, relative to the Prefect repository root.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print suggestions as JSON instead of human-readable text.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = [normalize_path(path) for path in args.paths if normalize_path(path)]
    result = build_result(paths)
    print(as_json(result) if args.json else as_text(result))


if __name__ == "__main__":
    main()
