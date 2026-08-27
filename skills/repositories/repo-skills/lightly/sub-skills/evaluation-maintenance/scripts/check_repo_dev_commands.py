#!/usr/bin/env python3
"""Plan LightlySSL repository-development commands without executing them.

The planner accepts changed paths or explicit categories and prints a scoped
maintenance plan. It never runs pytest, make, git, or package-management
commands.
"""

from __future__ import annotations

import argparse
import json
import shlex
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Iterable, Sequence

CATEGORY_CHOICES = (
    "benchmarking",
    "loss",
    "transforms",
    "models",
    "data",
    "cli",
    "embedding",
    "tests",
    "distributed",
    "examples",
    "docs",
    "benchmarks",
    "metadata",
    "ci",
    "release",
    "general",
)

TARGETED_TESTS = {
    "benchmarking": "python -m pytest tests/utils/benchmarking -q",
    "loss": "python -m pytest tests/loss -q",
    "transforms": "python -m pytest tests/transforms -q",
    "models": "python -m pytest tests/models -q",
    "data": "python -m pytest tests/data -q",
    "cli": "python -m pytest tests/cli -q",
    "embedding": "python -m pytest tests/embedding -q",
}

CATEGORY_EXPLANATIONS = {
    "benchmarking": "Benchmarking/evaluation helpers changed; run focused utility tests before broader package checks.",
    "loss": "Loss implementations or tests changed; run the loss subtree and formatting checks.",
    "transforms": "Transforms changed; verify transform output contracts and formatting.",
    "models": "Model or module code changed; verify model tests, adding optional TIMM checks only if that extra is installed.",
    "data": "Dataset/collate code changed; run data tests and gate video tests on the optional video extra.",
    "cli": "CLI/config/high-level API code changed; run CLI tests and route artifact-writing command details through CLI guidance.",
    "embedding": "Embedding APIs or callbacks changed; run embedding tests.",
    "tests": "Tests changed; run changed test files first, then the owning subtree if behavior is broad.",
    "distributed": "Distributed/DDP behavior changed; use the dedicated gloo-pool command with python -m pytest.",
    "examples": "Example scripts changed; regenerate tracked notebooks and inspect notebook diffs.",
    "docs": "Documentation changed; run no-plot docs build with dev/docs dependencies installed.",
    "benchmarks": "Benchmark scripts changed; keep validation static or tiny unless data/hardware/budget are explicit.",
    "metadata": "Dependency/package metadata changed; add dependency-variant checks in a disposable environment when needed.",
    "ci": "CI or Makefile behavior changed; mirror affected workflow commands without running release operations.",
    "release": "Release or notification workflows changed; treat publishing/deployment as maintainer-owned and credential-bound.",
    "general": "General package change; start with static checks and the most relevant targeted tests.",
}


@dataclass
class Plan:
    categories: set[str] = field(default_factory=set)
    commands: list[str] = field(default_factory=list)
    optional_commands: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def add_command(self, command: str) -> None:
        if command not in self.commands:
            self.commands.append(command)

    def add_optional(self, command: str) -> None:
        if command not in self.optional_commands and command not in self.commands:
            self.optional_commands.append(command)

    def add_warning(self, warning: str) -> None:
        if warning not in self.warnings:
            self.warnings.append(warning)

    def add_note(self, note: str) -> None:
        if note not in self.notes:
            self.notes.append(note)


def normalize_path(path: str) -> str:
    """Return a stable POSIX-looking path for classification."""
    path = path.strip().replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    if path.startswith("/"):
        # Only the suffix matters for category detection. Do not print absolute
        # paths in generated commands. Prefer repository top-level folders before
        # the package folder because many checkouts are themselves named "lightly".
        for label in ("tests", "examples", "docs", "benchmarks", ".github"):
            anchor = f"/{label}/"
            if anchor in path:
                suffix = path.rsplit(anchor, maxsplit=1)[1]
                return f"{label}/{suffix}"
        if "/lightly/" in path:
            suffix = path.rsplit("/lightly/", maxsplit=1)[1]
            metadata_files = {
                "pyproject.toml",
                "setup.py",
                "setup.cfg",
                "MANIFEST.in",
                "requirements.txt",
                "uv.lock",
                "Makefile",
            }
            if suffix in metadata_files:
                return suffix
            return f"lightly/{suffix}"
        return PurePosixPath(path).name
    return str(PurePosixPath(path))


def classify_path(path: str) -> set[str]:
    """Classify one changed path into maintenance categories."""
    p = normalize_path(path)
    categories: set[str] = set()
    lower = p.lower()

    if p.startswith("lightly/utils/benchmarking") or p.startswith(
        "tests/utils/benchmarking"
    ):
        categories.add("benchmarking")
    if p.startswith("lightly/loss") or p.startswith("tests/loss"):
        categories.add("loss")
    if p.startswith("lightly/transforms") or p.startswith("tests/transforms"):
        categories.add("transforms")
    if p.startswith("lightly/models") or p.startswith("tests/models"):
        categories.add("models")
    if p.startswith("lightly/data") or p.startswith("tests/data"):
        categories.add("data")
    if p.startswith("lightly/cli") or p in {"lightly/core.py"} or p.startswith(
        "tests/cli"
    ):
        categories.add("cli")
    if p.startswith("lightly/embedding") or p.startswith("tests/embedding"):
        categories.add("embedding")
    if p.startswith("tests/"):
        categories.add("tests")
    if "ddp" in lower or "dist" in lower or "distributed" in lower:
        categories.add("distributed")
    if p.startswith("examples/"):
        categories.add("examples")
    if p.startswith("docs/"):
        categories.add("docs")
    if p.startswith("benchmarks/"):
        categories.add("benchmarks")
    if p in {
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "MANIFEST.in",
        "requirements.txt",
        "uv.lock",
    }:
        categories.add("metadata")
    if p == "Makefile" or p.startswith(".github/workflows/"):
        categories.add("ci")
    if "release" in lower or "pypi" in lower or "notification" in lower:
        categories.add("release")
    if p.startswith("lightly/") and not categories:
        categories.add("general")

    return categories


def changed_test_files(paths: Iterable[str]) -> list[str]:
    """Return changed pytest files suitable for a targeted command."""
    result = []
    for raw_path in paths:
        path = normalize_path(raw_path)
        if path.startswith("tests/") and path.endswith(".py"):
            result.append(path)
    return sorted(set(result))


def quote_paths(paths: Sequence[str]) -> str:
    """Shell-quote path arguments."""
    return " ".join(shlex.quote(path) for path in paths)


def build_plan(args: argparse.Namespace) -> Plan:
    """Build a command plan from parsed arguments."""
    plan = Plan()
    normalized_paths = [normalize_path(path) for path in args.paths]

    for path in normalized_paths:
        plan.categories.update(classify_path(path))
    plan.categories.update(args.category or [])
    if not plan.categories:
        plan.categories.add("general")
        plan.add_note(
            "No changed paths or categories were supplied; using a conservative baseline plan."
        )

    if "release" in plan.categories:
        plan.add_warning(
            "Release, PyPI, deployment, and notification workflows are maintainer-owned; this planner will not suggest publishing or credentialed commands."
        )

    test_files = changed_test_files(normalized_paths)
    if test_files:
        command = "python -m pytest " + quote_paths(test_files) + " -q"
        plan.add_command(command)

    for category in (
        "benchmarking",
        "loss",
        "transforms",
        "models",
        "data",
        "cli",
        "embedding",
    ):
        if category in plan.categories:
            plan.add_command(TARGETED_TESTS[category])

    if "distributed" in plan.categories:
        plan.add_command("USE_PYTEST_POOL=1 python -m pytest tests --runslow -m DDP")
        plan.add_note(
            "DDP tests require USE_PYTEST_POOL=1 and python -m pytest so spawned workers can import the tests package."
        )

    if "examples" in plan.categories:
        plan.add_command("make generate-example-notebooks")
        plan.add_command("git diff -- examples/notebooks")
        plan.add_note(
            "Generated notebooks are tracked; update source examples, regenerate notebooks, and include notebook diffs."
        )

    if "docs" in plan.categories:
        plan.add_command("cd docs && make html-noplot")
        if args.docs_clean:
            plan.add_command("cd docs && make clean-html-noplot")
        else:
            plan.add_optional("cd docs && make clean-html-noplot")

    if "benchmarks" in plan.categories:
        plan.add_warning(
            "Do not run ImageNet-scale benchmark scripts as smoke tests without explicit dataset, hardware, runtime, and output policy."
        )

    source_like = plan.categories.intersection(
        {
            "benchmarking",
            "loss",
            "transforms",
            "models",
            "data",
            "cli",
            "embedding",
            "examples",
            "docs",
            "benchmarks",
            "general",
        }
    )
    if source_like or "tests" in plan.categories or "ci" in plan.categories:
        plan.add_command("make format-check")

    if source_like or "metadata" in plan.categories or "ci" in plan.categories:
        plan.add_command("make type-check")

    if "metadata" in plan.categories or "ci" in plan.categories or args.full:
        plan.add_command("make test-fast")
        plan.add_note(
            "Package metadata and CI changes can affect many workflows; use a disposable environment for install-variant checks."
        )

    if args.full:
        plan.add_command("make all-checks")
    else:
        plan.add_optional("make all-checks")

    if args.ci_parity:
        plan.add_optional("make install-minimal")
        plan.add_optional("make install-minimal-extras")
        plan.add_optional("make install-pinned")
        plan.add_optional("make install-pinned-extras")
        plan.add_optional("make install-latest")
        plan.add_warning(
            "CI-parity install targets reinstall dependencies; run them only in a disposable virtual environment."
        )

    for category in sorted(plan.categories):
        explanation = CATEGORY_EXPLANATIONS.get(category)
        if explanation:
            plan.add_note(explanation)

    return plan


def render_markdown(plan: Plan) -> str:
    """Render the plan as Markdown."""
    lines = ["# LightlySSL repository command plan", ""]
    lines.append("Categories: " + ", ".join(sorted(plan.categories)))
    lines.append("")
    if plan.warnings:
        lines.append("## Warnings")
        for warning in plan.warnings:
            lines.append(f"- {warning}")
        lines.append("")
    lines.append("## Recommended commands")
    for command in plan.commands:
        lines.append(f"- `{command}`")
    if not plan.commands:
        lines.append("- No concrete command was selected; provide changed paths or categories.")
    lines.append("")
    if plan.optional_commands:
        lines.append("## Optional escalation")
        for command in plan.optional_commands:
            lines.append(f"- `{command}`")
        lines.append("")
    if plan.notes:
        lines.append("## Notes")
        for note in plan.notes:
            lines.append(f"- {note}")
        lines.append("")
    lines.append("This planner does not execute commands.")
    return "\n".join(lines)


def render_json(plan: Plan) -> str:
    """Render the plan as deterministic JSON."""
    payload = {
        "categories": sorted(plan.categories),
        "commands": plan.commands,
        "optional_commands": plan.optional_commands,
        "warnings": plan.warnings,
        "notes": plan.notes,
        "executes_commands": False,
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Print a scoped LightlySSL maintenance command plan for changed paths. "
            "The planner never executes the recommended commands."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Changed files or directories, relative to a Lightly repository root.",
    )
    parser.add_argument(
        "--category",
        action="append",
        choices=CATEGORY_CHOICES,
        help="Add an explicit change category when no concrete path is available.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Include broad pre-PR checks such as make all-checks.",
    )
    parser.add_argument(
        "--ci-parity",
        action="store_true",
        help="Print optional dependency-variant install commands for disposable environments.",
    )
    parser.add_argument(
        "--docs-clean",
        action="store_true",
        help="Prefer the clean no-plot docs build over listing it as optional.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of Markdown.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    args = parse_args(argv)
    plan = build_plan(args)
    if args.json:
        print(render_json(plan))
    else:
        print(render_markdown(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
