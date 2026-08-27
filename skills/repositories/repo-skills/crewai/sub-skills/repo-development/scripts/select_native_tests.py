#!/usr/bin/env python3
"""Suggest safe CrewAI native verification commands from changed paths.

The script is intentionally read-only. It accepts paths as arguments or from
stdin, classifies them by CrewAI package/docs area, and prints focused pytest,
lint, type-check, and docs validation suggestions. It never runs git, tests,
release tooling, network calls, LLM calls, or credential-backed commands.
"""

from __future__ import annotations

import argparse
from collections import OrderedDict
from dataclasses import dataclass
import sys
from typing import Iterable


@dataclass(frozen=True)
class Suggestion:
    """A command suggestion plus safety context."""

    command: str
    reason: str


@dataclass(frozen=True)
class Finding:
    """A non-command advisory finding."""

    level: str
    message: str


PACKAGE_SOURCE_PREFIXES = (
    "lib/crewai/src/",
    "lib/cli/src/",
    "lib/crewai-tools/src/",
    "lib/crewai-files/src/",
    "lib/crewai-core/src/",
    "lib/devtools/src/",
)

DOCS_EDGE_PREFIX = "docs/edge/"
DOCS_FROZEN_PREFIX = "docs/v"
DOCS_IMAGES_PREFIX = "docs/images/"


class OrderedSuggestions:
    """Keep suggestions unique while preserving insertion order."""

    def __init__(self) -> None:
        self._items: OrderedDict[str, Suggestion] = OrderedDict()

    def add(self, command: str, reason: str) -> None:
        self._items.setdefault(command, Suggestion(command, reason))

    def __iter__(self) -> Iterable[Suggestion]:
        return iter(self._items.values())

    def __bool__(self) -> bool:
        return bool(self._items)


def normalize_path(raw_path: str) -> str:
    """Normalize a user-provided path or git name-status line."""
    text = raw_path.strip()
    if not text:
        return ""

    parts = text.split()
    if len(parts) >= 2 and parts[0][0] in {"A", "C", "D", "M", "R", "T", "U"}:
        # For rename/copy name-status lines, use the destination path.
        return parts[-1].replace("\\", "/")
    return text.replace("\\", "/")


def read_paths(args: argparse.Namespace) -> list[str]:
    """Collect changed paths from arguments and optional stdin."""
    values: list[str] = []
    values.extend(args.changed_file or [])
    values.extend(args.paths or [])

    if args.stdin:
        values.extend(sys.stdin.read().splitlines())

    normalized = [normalize_path(value) for value in values]
    return [path for path in normalized if path]


def add_docs_suggestions(path: str, suggestions: OrderedSuggestions, findings: list[Finding]) -> None:
    """Classify documentation paths."""
    if path.startswith(DOCS_FROZEN_PREFIX):
        findings.append(
            Finding(
                "BLOCKER",
                f"{path}: normal development must not edit frozen docs snapshots; move intended changes to docs/edge/<lang>/... unless this is an explicit release-cut docs-freeze task.",
            )
        )
        return

    if path.startswith(DOCS_IMAGES_PREFIX):
        findings.append(
            Finding(
                "CAUTION",
                f"{path}: docs images are append-only; adding a new file is safe, but deleting or renaming an existing image should be reverted.",
            )
        )
        suggestions.add(
            "cd docs && mintlify broken-links",
            "Validate docs references after image or MDX changes when Mintlify is installed.",
        )
        return

    if path.startswith(DOCS_EDGE_PREFIX) or path == "docs/docs.json":
        suggestions.add(
            "cd docs && mintlify broken-links",
            "Validate Mintlify navigation, links, and redirects for Edge docs changes when Mintlify is installed.",
        )
        if path == "docs/docs.json":
            suggestions.add(
                "uv run pytest lib/devtools/tests/test_docs_versioning.py -q",
                "Docs navigation/redirect changes may affect versioning and canonical URL behavior.",
            )
        return

    if path.startswith("scripts/docs/"):
        suggestions.add(
            "uv run pytest lib/devtools/tests/test_docs_versioning.py -q",
            "Docs scripts are release/versioning adjacent; validate behavior with tests rather than running freeze scripts.",
        )
        findings.append(
            Finding(
                "CAUTION",
                f"{path}: docs freeze and migration scripts mutate versioned docs or are one-time migrations; do not run them unless explicitly in release-cut context.",
            )
        )


def add_package_suggestions(path: str, suggestions: OrderedSuggestions) -> None:
    """Classify package and test paths."""
    if path == "pyproject.toml" or path.endswith("/pyproject.toml"):
        suggestions.add(
            "uv run pytest lib/devtools/tests/test_toml_updates.py -q",
            "Package metadata or workspace pins changed; validate version/dependency rewrite helpers.",
        )
        suggestions.add(
            f"uv run ruff check --no-fix {path}",
            "Check TOML-adjacent changed path context without applying ruff fixes to Python files.",
        )
        return

    if path.startswith("lib/cli/"):
        suggestions.add("uv run pytest lib/cli/tests/test_cli.py -q", "CLI package changed; verify command group loading.")
        if "create" in path or "template" in path:
            suggestions.add("uv run pytest lib/cli/tests/test_create_crew.py -q", "Scaffolding/template changes should keep crew creation tests green.")
            suggestions.add("uv run pytest lib/cli/tests/test_run_flow_definition.py -q", "Flow project definitions may be affected by template or CLI changes.")
        if "run" in path:
            suggestions.add("uv run pytest lib/cli/tests/test_run_crew.py -q", "Run command changes need focused run-command coverage without executing arbitrary projects.")
        if "train" in path:
            suggestions.add("uv run pytest lib/cli/tests/test_train_crew.py -q", "Training command changes need focused mocked tests.")
        if "test" in path:
            suggestions.add("uv run pytest lib/cli/tests/test_crew_test.py -q", "Crew test command changes need focused CLI test coverage.")
        if "deploy" in path:
            suggestions.add("uv run pytest lib/cli/tests/deploy/test_validate.py -q", "Deploy validation changes should use validation tests before hosted deploy commands.")
        if "tool" in path:
            suggestions.add("uv run pytest lib/cli/tests/tools/test_main.py -q", "Tool command changes should use CLI tool-command tests.")
        if "auth" in path or "login" in path or "logout" in path:
            suggestions.add("uv run pytest lib/cli/tests/authentication/test_auth_main.py -q", "Auth command changes should use mocked authentication tests.")
        suggestions.add("crewai --help", "Help output is a safe installed CLI smoke check.")
        return

    if path.startswith("lib/devtools/"):
        suggestions.add("uv run pytest lib/devtools/tests/test_docs_versioning.py -q", "Devtools docs versioning behavior should be validated through tests.")
        suggestions.add("uv run pytest lib/devtools/tests/test_toml_updates.py -q", "Devtools package/version metadata behavior should be validated through tests.")
        return

    if path.startswith("lib/crewai-files/"):
        suggestions.add("uv run pytest lib/crewai-files/tests/test_resolver.py -q", "File package changes should validate resolver behavior.")
        suggestions.add("uv run pytest lib/crewai/tests/test_agent_multimodal.py -q", "CrewAI integration with multimodal agents may be affected.")
        return

    if path.startswith("lib/crewai-tools/"):
        suggestions.add("uv run pytest lib/crewai-tools/tests/base_tool_test.py -q", "Tool package changes should validate base tool behavior.")
        if "rag" in path.lower():
            suggestions.add("uv run pytest lib/crewai-tools/tests/rag -q", "RAG loader changes should use focused loader tests.")
        if "mcp" in path.lower():
            suggestions.add("uv run pytest lib/crewai/tests/mcp/test_mcp_config.py -q", "MCP-adjacent tool changes should keep native MCP config behavior stable.")
        return

    if path.startswith("lib/crewai-core/"):
        suggestions.add("uv run pytest lib/crewai-core/tests -q", "Shared core utility changes should use crewai-core tests.")
        return

    if path.startswith("lib/crewai/"):
        suggestions.add("uv run pytest lib/crewai/tests/test_imports.py -q", "Core runtime package changes should keep public imports stable.")
        lower_path = path.lower()
        if "flow" in lower_path:
            suggestions.add("uv run pytest lib/crewai/tests/test_flow.py -q", "Flow changes should validate decorator/routing behavior.")
            suggestions.add("uv run pytest lib/crewai/tests/events/test_event_ordering.py -q", "Flow/event changes may affect event ordering.")
        if "event" in lower_path:
            suggestions.add("uv run pytest lib/crewai/tests/events/test_event_ordering.py -q", "Event changes should validate event ordering.")
        if "hook" in lower_path:
            suggestions.add("uv run pytest lib/crewai/tests/hooks/test_decorators.py -q", "Hook changes should validate decorator behavior.")
            suggestions.add("uv run pytest lib/crewai/tests/hooks/test_llm_hooks.py -q", "LLM hook changes should keep hook contracts stable.")
            suggestions.add("uv run pytest lib/crewai/tests/hooks/test_tool_hooks.py -q", "Tool hook changes should keep hook contracts stable.")
        if "llm" in lower_path:
            suggestions.add("uv run pytest lib/crewai/tests/test_custom_llm.py -q", "LLM changes should validate custom LLM behavior.")
            suggestions.add("uv run pytest lib/crewai/tests/test_streaming.py -q", "LLM streaming changes should validate streaming behavior.")
        if "mcp" in lower_path:
            suggestions.add("uv run pytest lib/crewai/tests/mcp/test_mcp_config.py -q", "MCP changes should validate config behavior.")
        if "memory" in lower_path:
            suggestions.add("uv run pytest lib/crewai/tests/memory -q", "Memory changes should use focused memory tests.")
        if "knowledge" in lower_path:
            suggestions.add("uv run pytest lib/crewai/tests/knowledge -q", "Knowledge changes should use focused knowledge tests.")
        if "rag" in lower_path:
            suggestions.add("uv run pytest lib/crewai/tests/rag -q", "RAG changes should use focused RAG tests.")
        if "task" in lower_path:
            suggestions.add("uv run pytest lib/crewai/tests/test_task.py lib/crewai/tests/test_task_guardrails.py -q", "Task changes should validate task and guardrail behavior.")
        if "crew" in lower_path:
            suggestions.add("uv run pytest lib/crewai/tests/test_crew.py -q", "Crew changes should validate crew construction and kickoff behavior.")
        if "checkpoint" in lower_path:
            suggestions.add("uv run pytest lib/crewai/tests/test_checkpoint.py -q", "Checkpoint changes should validate checkpoint behavior.")


def add_lint_suggestions(paths: list[str], suggestions: OrderedSuggestions) -> None:
    """Add conservative ruff/mypy suggestions for changed source files."""
    python_paths = [path for path in paths if path.endswith(".py")]
    source_paths = [path for path in python_paths if path.startswith(PACKAGE_SOURCE_PREFIXES)]

    if python_paths:
        joined = " ".join(python_paths[:12])
        suggestions.add(
            f"uv run ruff check --no-fix {joined}",
            "Run ruff diagnostics on changed Python files without applying automatic fixes.",
        )

    if source_paths:
        roots: list[str] = []
        for prefix in PACKAGE_SOURCE_PREFIXES:
            if any(path.startswith(prefix) for path in source_paths):
                roots.append(prefix.rstrip("/"))
        joined_roots = " ".join(roots)
        suggestions.add(
            f"uv run mypy {joined_roots}",
            "Strict mypy is configured for package source paths; run it on affected source roots when practical.",
        )


def build_report(paths: list[str]) -> tuple[list[Finding], OrderedSuggestions]:
    """Build advisory findings and safe command suggestions."""
    findings: list[Finding] = []
    suggestions = OrderedSuggestions()

    for path in paths:
        add_docs_suggestions(path, suggestions, findings)
        add_package_suggestions(path, suggestions)

    add_lint_suggestions(paths, suggestions)

    return findings, suggestions


def print_report(paths: list[str], findings: list[Finding], suggestions: OrderedSuggestions) -> int:
    """Print a human-readable report and return an exit code."""
    print("CrewAI native verification suggestions")
    print("=" * 39)
    print()

    if paths:
        print("Changed paths considered:")
        for path in paths:
            print(f"- {path}")
    else:
        print("No changed paths were provided.")
    print()

    if findings:
        print("Findings:")
        for finding in findings:
            print(f"- {finding.level}: {finding.message}")
        print()

    if suggestions:
        print("Suggested focused checks:")
        for item in suggestions:
            print(f"- {item.command}")
            print(f"  Reason: {item.reason}")
    else:
        print("Suggested focused checks:")
        print("- No area-specific checks matched. Start with the nearest package tests and `uv run ruff check --no-fix <changed-files>`.")

    print()
    print("Safety notes:")
    print("- This script only suggests commands; it does not run them.")
    print("- Do not run docs freeze scripts unless this is an explicit release-cut docs-freeze task.")
    print("- Do not run LLM-, credential-, deployment-, or network-backed commands without user approval.")

    return 2 if any(finding.level == "BLOCKER" for finding in findings) else 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Suggest safe focused CrewAI repo checks from changed paths without running them.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Changed file paths, or git name-status lines quoted as individual arguments.",
    )
    parser.add_argument(
        "--changed-file",
        action="append",
        help="Add a changed file path. Can be repeated.",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read additional changed paths or git name-status lines from standard input.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    paths = read_paths(args)
    findings, suggestions = build_report(paths)
    return print_report(paths, findings, suggestions)


if __name__ == "__main__":
    raise SystemExit(main())
