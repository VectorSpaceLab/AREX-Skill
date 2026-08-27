#!/usr/bin/env python3
"""Recommend targeted ZenML maintenance checks for changed paths.

The script is intentionally read-only: it prints commands but never runs them.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Recommendation:
    """A command recommendation with a short reason."""

    command: str
    reason: str
    caution: str | None = None


@dataclass
class Context:
    """Classified changed-path context."""

    paths: list[str]
    python_files: list[str] = field(default_factory=list)
    docs_paths: list[str] = field(default_factory=list)
    tests_paths: list[str] = field(default_factory=list)
    workflow_paths: list[str] = field(default_factory=list)
    migration_paths: list[str] = field(default_factory=list)
    script_paths: list[str] = field(default_factory=list)
    src_roots: set[str] = field(default_factory=set)
    areas: set[str] = field(default_factory=set)


def normalize_path(path: str) -> str:
    """Normalize a user-supplied path for portable matching."""

    normalized = path.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.strip("/")


def starts_with(path: str, prefix: str) -> bool:
    """Return whether a normalized path belongs to a normalized prefix."""

    return path == prefix or path.startswith(f"{prefix}/")


def classify(paths: Sequence[str]) -> Context:
    """Classify changed paths into ZenML maintenance areas."""

    context = Context(paths=[normalize_path(path) for path in paths])

    for path in context.paths:
        suffix = PurePosixPath(path).suffix
        if suffix == ".py":
            context.python_files.append(path)
        if starts_with(path, "docs/book"):
            context.docs_paths.append(path)
            context.areas.add("docs")
        if starts_with(path, "tests"):
            context.tests_paths.append(path)
            context.areas.add("tests")
        if starts_with(path, ".github/workflows") or path.endswith(
            (".yml", ".yaml")
        ):
            context.workflow_paths.append(path)
            context.areas.add("workflows")
        if starts_with(path, "src/zenml/zen_stores/migrations"):
            context.migration_paths.append(path)
            context.areas.add("migrations")
        if starts_with(path, "scripts") or path in {"zen-dev", "zen-test"}:
            context.script_paths.append(path)
            context.areas.add("scripts")

        if starts_with(path, "src/zenml/cli"):
            context.areas.add("cli")
            context.src_roots.add("src/zenml/cli")
        elif starts_with(path, "src/zenml/integrations"):
            context.areas.add("integrations")
            parts = path.split("/")
            if len(parts) >= 4:
                context.src_roots.add("/".join(parts[:4]))
            else:
                context.src_roots.add("src/zenml/integrations")
        elif starts_with(path, "src/zenml/orchestrators"):
            context.areas.add("orchestrators")
            context.src_roots.add("src/zenml/orchestrators")
        elif starts_with(path, "src/zenml/models"):
            context.areas.add("models")
            context.src_roots.add("src/zenml/models")
        elif starts_with(path, "src/zenml/zen_server"):
            context.areas.add("server")
            context.src_roots.add("src/zenml/zen_server")
        elif starts_with(path, "src/zenml/zen_stores"):
            context.areas.add("stores")
            context.src_roots.add("src/zenml/zen_stores")
        elif starts_with(path, "src/zenml"):
            context.areas.add("core")
            context.src_roots.add("src/zenml")
        elif path == "pyproject.toml":
            context.areas.add("dependencies")

    return context


def unique(items: Iterable[str]) -> list[str]:
    """Return items in first-seen order without duplicates."""

    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def shell_join(items: Iterable[str]) -> str:
    """Join path-like arguments for human-readable shell commands."""

    return " ".join(unique(item for item in items if item))


def test_targets(context: Context) -> list[str]:
    """Infer focused pytest targets from changed paths."""

    targets: list[str] = []
    targets.extend(path for path in context.tests_paths if path.endswith(".py"))

    if "cli" in context.areas:
        targets.append("tests/unit/cli")
    if "models" in context.areas:
        targets.append("tests/unit/models")
    if "server" in context.areas:
        targets.append("tests/unit/zen_server")
    if "stores" in context.areas or "migrations" in context.areas:
        targets.append("tests/unit/zen_stores")
    if "orchestrators" in context.areas:
        targets.append("tests/unit/orchestrators")
    if "integrations" in context.areas:
        targets.append("tests/integration/integrations/<integration>/<target_test>.py")
    if "core" in context.areas and not targets:
        targets.append("tests/unit/<target_test>.py")

    return unique(targets)


def recommendations(context: Context) -> list[Recommendation]:
    """Build ordered command recommendations for classified paths."""

    recs: list[Recommendation] = []

    if not context.paths:
        recs.append(
            Recommendation(
                "python skills/zenml/sub-skills/maintenance/scripts/choose_targeted_checks.py <changed paths>",
                "Pass changed paths to get focused ZenML check suggestions.",
            )
        )
        return recs

    py_compile_targets = [
        path
        for path in context.python_files
        if not starts_with(path, "tests") and not starts_with(path, "docs")
    ]
    if py_compile_targets:
        recs.append(
            Recommendation(
                f"python -m py_compile {shell_join(py_compile_targets)}",
                "Fast syntax/import-bytecode check for changed Python files.",
            )
        )

    tests = test_targets(context)
    if tests:
        recs.append(
            Recommendation(
                f"pytest {shell_join(tests)}",
                "Focused pytest target inferred from changed tests or source area.",
                "Avoid broad `pytest` or full `tests/integration` unless explicitly needed.",
            )
        )

    format_targets = unique(
        path
        for path in context.paths
        if starts_with(path, "src")
        or starts_with(path, "tests")
        or starts_with(path, "examples")
        or starts_with(path, "docs")
        or starts_with(path, "scripts")
        or starts_with(path, ".github")
        or path in {"pyproject.toml", "zen-dev", "zen-test"}
    )
    if format_targets:
        recs.append(
            Recommendation(
                f"bash scripts/format.sh {shell_join(format_targets)}",
                "Formats imports, code, and supported YAML for touched paths.",
                "This mutates files; use `--no-yamlfix` if YAML tooling is unavailable.",
            )
        )

    lint_targets = unique(context.src_roots | set(context.tests_paths))
    if lint_targets:
        recs.append(
            Recommendation(
                f"ruff check {shell_join(sorted(lint_targets))}",
                "Scoped Ruff check for changed source/test areas.",
            )
        )
        recs.append(
            Recommendation(
                f"ruff format {shell_join(sorted(lint_targets))} --check",
                "Scoped formatting verification after formatting.",
            )
        )

    mypy_targets = sorted(context.src_roots)
    if mypy_targets:
        recs.append(
            Recommendation(
                f"mypy {shell_join(mypy_targets)}",
                "Scoped type check for changed ZenML source areas.",
                "May require dev dependencies and optional extras for some integrations.",
            )
        )

    if context.docs_paths:
        recs.extend(
            [
                Recommendation(
                    "python scripts/check_relative_links.py",
                    "Checks repository-relative Markdown links after docs edits.",
                ),
                Recommendation(
                    "lychee --offline --no-progress 'docs/book/**/*.md'",
                    "Checks local docs links, images, and HTML references without external network.",
                    "Requires lychee; external URL checks can have bot-block false positives.",
                ),
                Recommendation(
                    "bash scripts/check-spelling.sh",
                    "Validates US English spelling and project dictionary rules.",
                    "Requires spelling toolchain from dev dependencies.",
                ),
            ]
        )

    if context.workflow_paths:
        recs.extend(
            [
                Recommendation(
                    "yamlfix --check .github tests",
                    "Checks workflow/YAML formatting in the same family as lint CI.",
                    "Skip or use format script with `--no-yamlfix` if yamlfix is unavailable.",
                ),
                Recommendation(
                    "GH_TOKEN=$(gh auth token) bash scripts/lint.sh",
                    "Runs GitHub Actions security linting when workflow files changed.",
                    "Only run when authenticated; never invent or print tokens.",
                ),
            ]
        )

    if context.migration_paths:
        recs.extend(
            [
                Recommendation(
                    "bash scripts/check-alembic-branches.sh",
                    "Detects diverging Alembic migration heads.",
                    "Requires Alembic from local/server dependencies.",
                ),
                Recommendation(
                    "alembic upgrade head",
                    "Validates migration upgrade path for the configured database.",
                    "Mutates the configured database; use an isolated test database.",
                ),
            ]
        )

    if "integrations" in context.areas:
        recs.append(
            Recommendation(
                "python skills/zenml/sub-skills/stacks-and-integrations/scripts/check_optional_imports.py --help",
                "Review optional-import checker usage before finishing integration flavor changes.",
                "Run the checker only from an active checkout with the needed dependencies.",
            )
        )

    if "dependencies" in context.areas:
        recs.append(
            Recommendation(
                "uv pip install --dry-run -e '.[server,dev]'",
                "Dry-runs dependency resolution for maintainer extras after dependency edits.",
                "Use the smallest relevant extra for integration-specific dependency changes.",
            )
        )

    return recs


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Recommend targeted ZenML maintenance checks for changed paths. "
            "The script prints commands only and never runs them."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Changed files or directories relative to a ZenML checkout.",
    )
    parser.add_argument(
        "--show-areas",
        action="store_true",
        help="Print inferred maintenance areas before recommendations.",
    )
    return parser


def print_recommendations(
    context: Context, recs: Sequence[Recommendation], show_areas: bool
) -> None:
    """Print recommendations in a stable human-readable format."""

    if show_areas:
        areas = ", ".join(sorted(context.areas)) or "none"
        print(f"Inferred areas: {areas}")
        if context.src_roots:
            print(f"Source roots: {shell_join(sorted(context.src_roots))}")
        print()

    print("Recommended targeted checks (not executed):")
    for index, rec in enumerate(recs, start=1):
        print(f"{index}. {rec.command}")
        print(f"   Reason: {rec.reason}")
        if rec.caution:
            print(f"   Caution: {rec.caution}")

    print()
    print("Always review suggestions against the actual change and AGENTS rules.")
    print("Do not run broad or mutating checks without user approval.")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the recommendation CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)
    context = classify(args.paths)
    print_recommendations(context, recommendations(context), args.show_areas)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
