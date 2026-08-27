#!/usr/bin/env python3
"""Suggest focused DVC pytest targets for changed paths.

This helper is intentionally read-only: it does not import DVC, inspect the
working tree, or execute pytest. Pass changed file paths as arguments, or pipe
one path per line on stdin.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import PurePosixPath

DEFAULT_MARKER = "not studio and not needs_internet and not vscode"


@dataclass(frozen=True)
class Rule:
    prefixes: tuple[str, ...]
    targets: tuple[str, ...]
    reason: str
    avoid_markers: tuple[str, ...] = ()


@dataclass
class Suggestion:
    targets: set[str] = field(default_factory=set)
    reasons: list[str] = field(default_factory=list)
    avoid_markers: set[str] = field(default_factory=lambda: {"studio", "needs_internet", "vscode"})


RULES: tuple[Rule, ...] = (
    Rule(
        ("dvc/cli/",),
        ("tests/unit/cli", "tests/unit/command"),
        "CLI entry point, parser, or command base changed.",
    ),
    Rule(
        ("dvc/commands/experiments/",),
        (
            "tests/unit/command/test_experiments.py",
            "tests/unit/repo/experiments",
            "tests/func/experiments",
        ),
        "Experiment command wrapper changed.",
        ("studio", "vscode"),
    ),
    Rule(
        ("dvc/commands/queue/",),
        ("tests/unit/command/test_queue.py", "tests/func/experiments/test_queue.py"),
        "Experiment queue command wrapper changed.",
    ),
    Rule(
        ("dvc/commands/",),
        ("tests/unit/command",),
        "CLI command wrapper changed; add command-specific functional tests when available.",
    ),
    Rule(
        ("dvc/repo/experiments/",),
        ("tests/unit/repo/experiments", "tests/unit/command/test_experiments.py", "tests/func/experiments"),
        "Experiment repository logic changed.",
        ("studio", "vscode"),
    ),
    Rule(
        ("dvc/repo/metrics/",),
        ("tests/unit/command/test_metrics.py", "tests/func/metrics"),
        "Metrics repo logic changed.",
    ),
    Rule(
        ("dvc/repo/params/",),
        ("tests/unit/command/test_params.py", "tests/func/params"),
        "Params repo logic changed.",
    ),
    Rule(
        ("dvc/repo/plots/", "dvc/render/"),
        ("tests/unit/command/test_plots.py", "tests/func/plots", "tests/unit/render"),
        "Plots/rendering logic changed.",
        ("studio", "vscode"),
    ),
    Rule(
        ("dvc/repo/",),
        ("tests/unit/repo",),
        "Repository business logic changed; add matching tests/func target for the area.",
    ),
    Rule(
        ("dvc/api/",),
        ("tests/unit/test_api.py", "tests/func/api"),
        "Public Python API changed.",
    ),
    Rule(
        ("dvc/fs/",),
        ("tests/unit/fs", "tests/func/test_fs.py"),
        "Filesystem abstraction changed.",
    ),
    Rule(
        ("dvc/config.py", "dvc/config_schema.py", "dvc/schema.py"),
        ("tests/unit/test_config.py", "tests/func/test_config.py"),
        "Configuration or schema validation changed.",
    ),
    Rule(
        ("dvc/parsing/",),
        ("tests/func/parsing", "tests/unit/test_interpolate.py"),
        "Pipeline/config interpolation parsing changed.",
    ),
    Rule(
        ("dvc/stage/",),
        ("tests/unit/stage", "tests/func/test_stage.py", "tests/func/test_stage_load.py"),
        "Stage model, loader, runner, or serialization changed.",
    ),
    Rule(
        ("dvc/output.py",),
        ("tests/unit/output", "tests/func/test_checkout.py", "tests/func/test_commit.py"),
        "Output handling changed.",
    ),
    Rule(
        ("dvc/dependency/",),
        ("tests/unit/dependency", "tests/func/test_repro.py"),
        "Dependency handling changed.",
    ),
    Rule(
        ("dvc/dvcfile.py",),
        ("tests/unit/test_dvcfile.py", "tests/func/test_dvcfile.py", "tests/func/test_stage_load.py"),
        "DVC file load/dump behavior changed.",
    ),
    Rule(
        ("dvc/data_cloud.py", "dvc/cachemgr.py"),
        ("tests/func/test_data_cloud.py", "tests/func/test_remote.py", "tests/func/test_gc.py"),
        "Cloud/cache manager behavior changed; start with local remote fixtures.",
        ("needs_internet",),
    ),
    Rule(
        ("dvc/testing/", "tests/conftest.py", "tests/dir_helpers.py", "tests/scripts.py"),
        ("tests/unit", "tests/func/test_repo.py"),
        "Test fixture or harness changed; run a small representative unit and functional slice.",
    ),
    Rule(
        ("pyproject.toml",),
        ("tests/unit/cli", "tests/unit/command/test_help.py"),
        "Project metadata, pytest, ruff, or mypy config changed; choose additional checks for the edited section.",
    ),
)

COMMAND_TESTS = {
    "add": ("tests/unit/command/test_add.py", "tests/func/test_add.py"),
    "repro": ("tests/unit/command/test_repro.py", "tests/unit/repo/test_reproduce.py", "tests/func/repro"),
    "stage": ("tests/unit/command/test_stage.py", "tests/func/test_stage.py"),
    "status": ("tests/unit/command/test_status.py", "tests/func/test_status.py", "tests/func/test_data_status.py"),
    "remote": ("tests/unit/command/test_config.py", "tests/func/test_remote.py"),
    "metrics": ("tests/unit/command/test_metrics.py", "tests/func/metrics"),
    "params": ("tests/unit/command/test_params.py", "tests/func/params"),
    "plots": ("tests/unit/command/test_plots.py", "tests/func/plots"),
    "get": ("tests/unit/command/test_get.py", "tests/func/test_get.py"),
    "get_url": ("tests/unit/command/test_get_url.py", "tests/func/test_get_url.py"),
    "imp": ("tests/unit/command/test_imp.py", "tests/func/test_import.py"),
    "imp_url": ("tests/unit/command/test_imp_url.py", "tests/func/test_import_url.py"),
    "pull": ("tests/func/test_remote.py",),
    "push": ("tests/func/test_remote.py",),
    "fetch": ("tests/func/test_remote.py",),
    "gc": ("tests/unit/command/test_gc.py", "tests/func/test_gc.py"),
    "data": ("tests/unit/command/test_data_status.py", "tests/func/test_data_status.py"),
    "artifacts": ("tests/func/artifacts", "tests/func/api/test_artifacts.py"),
}

REPO_TESTS = {
    "add": COMMAND_TESTS["add"],
    "reproduce": COMMAND_TESTS["repro"],
    "run": ("tests/unit/test_run.py", "tests/func/test_run.py"),
    "status": COMMAND_TESTS["status"],
    "fetch": COMMAND_TESTS["fetch"],
    "pull": COMMAND_TESTS["pull"],
    "push": COMMAND_TESTS["push"],
    "gc": COMMAND_TESTS["gc"],
    "get": COMMAND_TESTS["get"],
    "get_url": COMMAND_TESTS["get_url"],
    "imp": COMMAND_TESTS["imp"],
    "imp_url": COMMAND_TESTS["imp_url"],
    "metrics": COMMAND_TESTS["metrics"],
    "params": COMMAND_TESTS["params"],
    "plots": COMMAND_TESTS["plots"],
}


def normalize(path: str) -> str:
    return PurePosixPath(path.replace("\\", "/")).as_posix().lstrip("./")


def add_rule_matches(path: str, suggestion: Suggestion) -> None:
    for rule in RULES:
        if any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in rule.prefixes):
            suggestion.targets.update(rule.targets)
            suggestion.reasons.append(f"{path}: {rule.reason}")
            suggestion.avoid_markers.update(rule.avoid_markers)


def add_name_matches(path: str, suggestion: Suggestion) -> None:
    parts = PurePosixPath(path).parts
    if len(parts) >= 3 and parts[0] == "dvc" and parts[1] == "commands":
        command_name = PurePosixPath(path).stem
        suggestion.targets.update(COMMAND_TESTS.get(command_name, ()))
        if command_name in COMMAND_TESTS:
            suggestion.reasons.append(f"{path}: matched command-specific tests for {command_name!r}.")
    if len(parts) >= 3 and parts[0] == "dvc" and parts[1] == "repo":
        area = PurePosixPath(path).stem
        suggestion.targets.update(REPO_TESTS.get(area, ()))
        if area in REPO_TESTS:
            suggestion.reasons.append(f"{path}: matched repo-area tests for {area!r}.")


def collect_paths(argv_paths: list[str]) -> list[str]:
    raw_paths = list(argv_paths)
    if not raw_paths and not sys.stdin.isatty():
        raw_paths.extend(line.strip() for line in sys.stdin if line.strip())
    return [normalize(path) for path in raw_paths if path.strip()]


def build_suggestion(paths: list[str]) -> Suggestion:
    suggestion = Suggestion()
    for path in paths:
        add_rule_matches(path, suggestion)
        add_name_matches(path, suggestion)
    if not suggestion.targets:
        suggestion.targets.update(("tests/unit",))
        suggestion.reasons.append("No specific mapping matched; start with nearby unit tests for the edited module.")
    return suggestion


def marker_expression(markers: set[str]) -> str:
    ordered = ["studio", "needs_internet", "vscode"]
    extras = sorted(marker for marker in markers if marker not in ordered and marker != "not studio")
    selected = [marker for marker in ordered if marker in markers] + extras
    return " and ".join(f"not {marker}" for marker in selected)


def print_suggestion(paths: list[str], suggestion: Suggestion) -> None:
    marker = marker_expression(suggestion.avoid_markers)
    targets = sorted(suggestion.targets)
    print("Changed paths:")
    for path in paths:
        print(f"  - {path}")
    print("\nSuggested pytest targets:")
    for target in targets:
        print(f"  - {target}")
    print("\nDefault marker exclusion:")
    print(f"  -m \"{marker}\"")
    print("\nSuggested command:")
    joined_targets = " ".join(targets)
    print(f"  python -m pytest {joined_targets} -m \"{marker}\"")
    print("\nWhy:")
    for reason in suggestion.reasons:
        print(f"  - {reason}")
    print("\nSafety notes:")
    print("  - This helper does not run tests.")
    print("  - Do not run Studio, network, VSCode, or cloud-backend tests unless the task explicitly needs them.")
    print("  - Add narrower node ids after inspecting the matching test files.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Changed file paths. If omitted, read newline-separated paths from stdin.")
    args = parser.parse_args()
    paths = collect_paths(args.paths)
    if not paths:
        parser.error("provide changed paths as arguments or on stdin")
    suggestion = build_suggestion(paths)
    print_suggestion(paths, suggestion)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
