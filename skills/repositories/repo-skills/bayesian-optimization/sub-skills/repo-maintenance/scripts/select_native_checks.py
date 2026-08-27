#!/usr/bin/env python3
"""Print safe native-check recommendations for a BayesianOptimization checkout.

The helper is deterministic and non-mutating: it only prints commands and safety
labels. Run commands yourself after reviewing the recommendation.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Iterable


@dataclass(frozen=True)
class CommandGroup:
    """A labeled group of commands to review and optionally run."""

    key: str
    label: str
    safety: str
    reason: str
    commands: tuple[str, ...]
    notes: tuple[str, ...] = field(default_factory=tuple)


GROUPS: dict[str, CommandGroup] = {
    "install-dev": CommandGroup(
        key="install-dev",
        label="Development environment",
        safety="SAFE setup; can resolve/install broad dev dependencies",
        reason="Needed for pytest, Ruff, notebooks, docs, and pre-commit parity with CI.",
        commands=("uv sync --extra dev",),
        notes=("Use a minimal `uv sync` only for import-only/runtime smoke checks.",),
    ),
    "lint": CommandGroup(
        key="lint",
        label="Non-mutating Ruff checks",
        safety="SAFE non-mutating verification",
        reason="Mirrors scripts/check.sh without changing files.",
        commands=(
            "uv run ruff format --check bayes_opt tests",
            "uv run ruff check bayes_opt tests",
        ),
    ),
    "unit-fast": CommandGroup(
        key="unit-fast",
        label="Broad unit tests except notebooks",
        safety="SAFE test execution; may take moderate time",
        reason="Covers package and test changes without slow notebook execution.",
        commands=("uv run pytest tests --ignore=tests/test_notebooks_run.py",),
    ),
    "ci-coverage": CommandGroup(
        key="ci-coverage",
        label="CI-like coverage run",
        safety="SAFE test execution after dev sync; may take moderate time",
        reason="Matches the test workflow command used after selecting a Python/NumPy lane.",
        commands=("uv run --no-sync pytest --cov-report xml --cov=bayes_opt/",),
        notes=(
            "For NumPy 1 lane, first run: uv pip install \"numpy>=1.25,<2\" \"scipy<1.18\"",
            "For NumPy 2 lane, first run: uv pip install \"numpy>=2\"",
            "Do not use NumPy 1 on Python 3.13 or newer.",
        ),
    ),
    "test-acquisition": CommandGroup(
        key="test-acquisition",
        label="Acquisition tests",
        safety="SAFE focused pytest",
        reason="Relevant to acquisition functions and constrained acquisition integration.",
        commands=("uv run pytest tests/test_acquisition.py",),
    ),
    "test-optimizer": CommandGroup(
        key="test-optimizer",
        label="Optimizer workflow tests",
        safety="SAFE focused pytest",
        reason="Relevant to BayesianOptimization orchestration, state, predict, bounds, and public API changes.",
        commands=("uv run pytest tests/test_bayesian_optimization.py",),
    ),
    "test-constraint": CommandGroup(
        key="test-constraint",
        label="Constraint tests",
        safety="SAFE focused pytest",
        reason="Relevant to constraint models and constrained optimization integration.",
        commands=(
            "uv run pytest tests/test_constraint.py",
            "uv run pytest tests/test_acquisition.py::test_integration_constrained",
        ),
    ),
    "test-domain": CommandGroup(
        key="test-domain",
        label="Sequential domain reduction tests",
        safety="SAFE focused pytest",
        reason="Relevant to SequentialDomainReductionTransformer and bounds trimming.",
        commands=("uv run pytest tests/test_seq_domain_red.py",),
    ),
    "test-parameter": CommandGroup(
        key="test-parameter",
        label="Typed parameter tests",
        safety="SAFE focused pytest",
        reason="Relevant to float/int/categorical parameters and kernel wrapping.",
        commands=("uv run pytest tests/test_parameter.py tests/test_target_space.py",),
    ),
    "test-target-space": CommandGroup(
        key="test-target-space",
        label="Target-space tests",
        safety="SAFE focused pytest",
        reason="Relevant to registration, bounds, conversion, random sampling, constraints, and result storage.",
        commands=("uv run pytest tests/test_target_space.py tests/test_bayesian_optimization.py",),
    ),
    "test-util": CommandGroup(
        key="test-util",
        label="Utility tests",
        safety="SAFE focused pytest",
        reason="Relevant to utility helpers such as random-state normalization.",
        commands=("uv run pytest tests/test_util.py",),
    ),
    "test-logger": CommandGroup(
        key="test-logger",
        label="Logger tests",
        safety="SAFE focused pytest",
        reason="Relevant to ScreenLogger behavior and terminal output formatting.",
        commands=("uv run pytest tests/test_logger.py",),
    ),
    "test-notebooks": CommandGroup(
        key="test-notebooks",
        label="Notebook execution tests",
        safety="SAFE but SLOW; executes notebooks with 600-second cell timeout",
        reason="Relevant to example notebooks and notebook/doc execution dependencies.",
        commands=("uv run pytest tests/test_notebooks_run.py",),
        notes=("Requires broad dev dependencies and a working Python kernel.",),
    ),
    "docs-html": CommandGroup(
        key="docs-html",
        label="Local docs build",
        safety="SAFE build; may create/update generated docs output outside skill tree",
        reason="Relevant to docsrc changes and Sphinx/autodoc/nbsphinx validation.",
        commands=("cd docsrc && uv run make html",),
        notes=("Install pandoc before reproducing the docs workflow exactly.",),
    ),
    "docs-github": CommandGroup(
        key="docs-github",
        label="Release-like docs target",
        safety="CAUTION: build target copies generated docs output",
        reason="Matches the docs workflow target more closely than make html.",
        commands=("cd docsrc && uv run make github",),
        notes=("Use only when validating workflow-like docs output.",),
    ),
    "precommit": CommandGroup(
        key="precommit",
        label="Pre-commit all-files check",
        safety="SAFE if hooks already available; does not install hooks",
        reason="Matches lint workflow behavior without running scripts/check_precommit.sh.",
        commands=("uv run pre-commit run --all-files --show-diff-on-failure --color=always",),
        notes=("Do not use scripts/check_precommit.sh for routine verification; it installs hooks.",),
    ),
    "build": CommandGroup(
        key="build",
        label="Package build validation",
        safety="SAFE local build; does not publish",
        reason="Relevant to pyproject/build-backend/package metadata changes.",
        commands=("uv build",),
        notes=("Publishing is release-only and secret-protected; do not run uv publish here.",),
    ),
}

MODULE_TESTS: dict[str, tuple[str, ...]] = {
    "acquisition.py": ("test-acquisition",),
    "bayesian_optimization.py": ("test-optimizer",),
    "constraint.py": ("test-constraint",),
    "domain_reduction.py": ("test-domain",),
    "parameter.py": ("test-parameter",),
    "target_space.py": ("test-target-space",),
    "util.py": ("test-util",),
    "logger.py": ("test-logger",),
    "exception.py": ("test-optimizer", "test-target-space", "test-acquisition"),
    "__init__.py": ("test-optimizer", "test-acquisition", "test-constraint"),
}

TEST_FILE_TO_GROUP: dict[str, str] = {
    "test_acquisition.py": "test-acquisition",
    "test_bayesian_optimization.py": "test-optimizer",
    "test_constraint.py": "test-constraint",
    "test_logger.py": "test-logger",
    "test_notebooks_run.py": "test-notebooks",
    "test_parameter.py": "test-parameter",
    "test_seq_domain_red.py": "test-domain",
    "test_target_space.py": "test-target-space",
    "test_util.py": "test-util",
}

CAPABILITY_GROUPS: dict[str, tuple[str, ...]] = {
    "runtime": ("unit-fast", "lint"),
    "lint": ("lint",),
    "precommit": ("precommit",),
    "notebooks": ("test-notebooks",),
    "docs": ("docs-html",),
    "docs-release": ("docs-github",),
    "matrix": ("ci-coverage",),
    "build": ("build",),
    "constraints": ("test-constraint",),
    "acquisition": ("test-acquisition",),
    "parameters": ("test-parameter",),
    "domain": ("test-domain",),
    "target-space": ("test-target-space",),
}

DEFAULT_ORDER = (
    "install-dev",
    "test-acquisition",
    "test-optimizer",
    "test-constraint",
    "test-domain",
    "test-parameter",
    "test-target-space",
    "test-util",
    "test-logger",
    "unit-fast",
    "test-notebooks",
    "docs-html",
    "docs-github",
    "lint",
    "precommit",
    "ci-coverage",
    "build",
)


def normalize_path(raw: str) -> PurePosixPath:
    """Normalize user-supplied paths to repository-relative POSIX-ish paths."""

    cleaned = raw.strip().replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return PurePosixPath(cleaned)


def add(group_keys: set[str], *keys: str) -> None:
    """Add known command group keys."""

    for key in keys:
        if key in GROUPS:
            group_keys.add(key)


def classify_path(path: PurePosixPath, group_keys: set[str], reasons: list[str]) -> None:
    """Classify one touched path into recommended command groups."""

    parts = path.parts
    name = path.name
    path_str = path.as_posix()

    if not parts:
        return

    if parts[0] in {"bayes_opt", "tests"} or path_str in {"ruff.toml", ".pre-commit-config.yaml"}:
        add(group_keys, "lint")

    if parts[0] == "bayes_opt":
        module_groups = MODULE_TESTS.get(name)
        if module_groups:
            add(group_keys, *module_groups)
            reasons.append(f"{path_str}: package module maps to {', '.join(module_groups)}")
        else:
            add(group_keys, "unit-fast")
            reasons.append(f"{path_str}: package change without a narrow mapping")

    elif parts[0] == "tests":
        mapped = TEST_FILE_TO_GROUP.get(name)
        if mapped:
            add(group_keys, mapped)
            reasons.append(f"{path_str}: edited native test maps to {mapped}")
        else:
            add(group_keys, "unit-fast")
            reasons.append(f"{path_str}: test change maps to broad unit tests")

    elif parts[0] == "examples":
        if name.endswith(".ipynb"):
            add(group_keys, "test-notebooks")
            reasons.append(f"{path_str}: notebook example maps to notebook execution tests")
        elif name.endswith(".py"):
            add(group_keys, "unit-fast")
            reasons.append(f"{path_str}: Python example maps to broad unit smoke coverage; run script manually if needed")
        else:
            add(group_keys, "unit-fast")
            reasons.append(f"{path_str}: example asset may need manual example validation")

    elif parts[0] == "docsrc" or name in {"README.md"}:
        add(group_keys, "docs-html")
        reasons.append(f"{path_str}: docs/readme change maps to local docs build")

    elif path_str in {"pyproject.toml", "uv.lock"}:
        add(group_keys, "unit-fast", "lint", "ci-coverage", "build")
        reasons.append(f"{path_str}: dependency/build metadata maps to tests, matrix lane, and local build validation")

    elif path_str in {"ruff.toml", ".pre-commit-config.yaml"}:
        add(group_keys, "lint", "precommit")
        reasons.append(f"{path_str}: lint configuration maps to Ruff/pre-commit checks")

    elif parts[0] == ".github" and "workflows" in parts:
        add(group_keys, "lint")
        if name == "run_tests.yml":
            add(group_keys, "ci-coverage")
        elif name == "build_docs.yml":
            add(group_keys, "docs-html")
        elif name == "format_and_lint.yml":
            add(group_keys, "precommit")
        elif name == "python-publish.yml":
            add(group_keys, "build")
        reasons.append(f"{path_str}: workflow change maps to the corresponding local non-publish checks")

    elif parts[0] == "scripts":
        add(group_keys, "lint", "precommit")
        reasons.append(f"{path_str}: maintenance script change maps to lint/pre-commit parity checks")

    else:
        add(group_keys, "unit-fast", "lint")
        reasons.append(f"{path_str}: unknown surface maps to conservative unit and lint checks")


def ordered_groups(keys: Iterable[str]) -> list[CommandGroup]:
    """Return command groups in stable review order."""

    key_set = set(keys)
    return [GROUPS[key] for key in DEFAULT_ORDER if key in key_set]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Print non-mutating recommended native checks for a BayesianOptimization checkout. "
            "Commands are not executed."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Touched repository-relative paths such as bayes_opt/acquisition.py or docsrc/index.rst.",
    )
    parser.add_argument(
        "--capability",
        action="append",
        choices=sorted(CAPABILITY_GROUPS),
        default=[],
        help="Add a capability surface explicitly; may be repeated.",
    )
    parser.add_argument(
        "--include-dev-sync",
        action="store_true",
        help="Include the CI-style dev dependency sync command at the top of the recommendation.",
    )
    parser.add_argument(
        "--include-precommit",
        action="store_true",
        help="Include a non-hook-installing pre-commit all-files command.",
    )
    parser.add_argument(
        "--include-docs-release-target",
        action="store_true",
        help="Include the release-like docs target `cd docsrc && uv run make github`.",
    )
    parser.add_argument(
        "--ci-matrix",
        action="store_true",
        help="Include CI-like coverage and Python/NumPy lane notes.",
    )
    parser.add_argument(
        "--all-unit",
        action="store_true",
        help="Include broad unit tests excluding notebooks.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    group_keys: set[str] = set()
    reasons: list[str] = []

    for raw_path in args.paths:
        classify_path(normalize_path(raw_path), group_keys, reasons)

    for capability in args.capability:
        add(group_keys, *CAPABILITY_GROUPS[capability])
        reasons.append(f"--capability {capability}: added {', '.join(CAPABILITY_GROUPS[capability])}")

    if args.include_dev_sync:
        add(group_keys, "install-dev")
        reasons.append("--include-dev-sync: added development environment setup")
    if args.include_precommit:
        add(group_keys, "precommit")
        reasons.append("--include-precommit: added all-files pre-commit verification without hook installation")
    if args.include_docs_release_target:
        add(group_keys, "docs-github")
        reasons.append("--include-docs-release-target: added release-like docs target")
    if args.ci_matrix:
        add(group_keys, "ci-coverage")
        reasons.append("--ci-matrix: added CI-like coverage and Python/NumPy lane notes")
    if args.all_unit:
        add(group_keys, "unit-fast")
        reasons.append("--all-unit: added broad unit suite excluding notebooks")

    if not group_keys:
        print("No touched paths or capability flags were supplied.")
        print("Suggested starter checks:")
        group_keys.update({"unit-fast", "lint"})

    print("BayesianOptimization native-check recommendation")
    print("Commands are printed for review only; this helper does not run them.")
    print()

    if reasons:
        print("Why these groups were selected:")
        for reason in reasons:
            print(f"- {reason}")
        print()

    for group in ordered_groups(group_keys):
        print(f"## {group.label}")
        print(f"Safety: {group.safety}")
        print(f"Reason: {group.reason}")
        for command in group.commands:
            print(f"$ {command}")
        for note in group.notes:
            print(f"Note: {note}")
        print()

    print("Excluded by design:")
    print("- scripts/check_precommit.sh: installs pre-commit hooks before checking all files.")
    print("- scripts/format.sh: formats/fixes source files and is intentionally mutating.")
    print("- PyPI upload: release-only and protected by repository secrets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
