#!/usr/bin/env python3
"""Suggest focused Ultralytics maintainer checks for changed repository paths."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Iterable


@dataclass(frozen=True)
class Recommendation:
    """A deterministic set of checks for one changed-path category."""

    category: str
    reason: str
    pytest: tuple[str, ...] = ()
    cli: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    extras: tuple[str, ...] = ()


@dataclass
class Plan:
    """Aggregated check plan."""

    categories: list[str] = field(default_factory=list)
    pytest: list[str] = field(default_factory=list)
    cli: list[str] = field(default_factory=list)
    extras: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def normalize_path(path: str) -> str:
    """Normalize a user-supplied changed path to a POSIX relative path."""

    normalized = path.replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.strip("/")


def has_prefix(path: str, *prefixes: str) -> bool:
    """Return True when a normalized path is equal to or inside any prefix."""

    return any(path == prefix.rstrip("/") or path.startswith(prefix.rstrip("/") + "/") for prefix in prefixes)


def recommendation_for(path: str) -> Recommendation:
    """Return the focused recommendation for one normalized path."""

    name = PurePosixPath(path).name

    if path in {"README.md", "CONTRIBUTING.md", "LICENSE"}:
        return Recommendation(
            "project docs",
            "Project-facing docs or license files need policy and markdown review.",
            cli=("ruff check README.md",) if path == "README.md" else (),
            notes=("Avoid weakening AGPL or CLA language without explicit maintainer direction.",),
        )

    if has_prefix(path, "docs") or path in {"mkdocs.yml", "mkdocs.yaml"}:
        return Recommendation(
            "docs",
            "Docs-only changes should use docs/style checks and skip ML tests by default.",
            cli=("ruff check <touched docs/source files>", "python docs/build_reference.py", "python docs/build_docs.py"),
            notes=(
                "Docs build scripts require dev/docs dependencies and may mutate generated output.",
                "Do not run training, export, CUDA, or media tests unless executable examples changed runtime behavior.",
            ),
            extras=("dev",),
        )

    if has_prefix(path, ".github/workflows"):
        return Recommendation(
            "ci workflows",
            "Workflow changes need YAML review and local equivalents for edited commands.",
            cli=("yolo --help",),
            notes=("Full GitHub Actions parity is usually not practical locally.",),
        )

    if path == "pyproject.toml":
        return Recommendation(
            "project config",
            "Tool, packaging, or optional-extra changes need metadata-aware focused checks.",
            pytest=("pytest tests/test_cli.py::test_special_modes", "pytest tests/test_exports.py::test_export_env_has_smoke"),
            cli=("python -m pip install -e .", "yolo --help", "yolo cfg"),
            notes=("Use disposable environments for install-matrix or heavyweight optional-extra validation.",),
        )

    if has_prefix(path, "tests"):
        test_path = path if path.endswith(".py") else "tests"
        return Recommendation(
            "tests",
            "Changed tests should run directly before adjacent subsystem coverage.",
            pytest=(f"pytest {test_path}",),
            notes=("Use exact test nodes when only one test changed.",),
        )

    if has_prefix(path, "ultralytics/engine"):
        if name == "exporter.py":
            return Recommendation(
                "export engine",
                "Exporter changes need export smoke coverage before backend matrices.",
                pytest=("pytest tests/test_exports.py::test_export_env_has_smoke", "pytest tests/test_engine.py::test_export"),
                notes=("Run backend-specific export tests only with matching export extras and runtimes.",),
                extras=("export-base for ONNX/OpenVINO smoke; backend-specific extras for heavier formats",),
            )
        if name == "results.py":
            return Recommendation(
                "engine results",
                "Results changes affect inference return objects but should not require export matrices.",
                pytest=("pytest tests/test_engine.py", "pytest tests/test_python.py::test_model_methods"),
                cli=("yolo --help",),
                notes=(
                    "Prefer exact Results-related nodes or a small direct Results smoke when available.",
                    "Do not run full export, CUDA, tracking video, or training tests unless the edit crosses those paths.",
                ),
            )
        return Recommendation(
            "engine",
            "Engine abstractions affect Model, Trainer, Validator, Predictor, Exporter, or shared behavior.",
            pytest=("pytest tests/test_engine.py", "pytest tests/test_python.py::test_model_methods"),
            notes=("Prefer exact test nodes near the edited class when known.",),
        )

    if has_prefix(path, "ultralytics/data"):
        return Recommendation(
            "data",
            "Data changes affect loaders, converters, augmentation, annotation, or dataset utilities.",
            pytest=(
                "pytest tests/test_python.py::test_data_utils",
                "pytest tests/test_python.py::test_safe_download_unzips_local_path_archive",
                "pytest tests/test_python.py::test_safe_download_skips_unsafe_archive_members",
            ),
            notes=("Dataset/training tests may download assets; run only when cache/downloads are allowed.",),
        )

    if has_prefix(path, "ultralytics/cfg/trackers", "ultralytics/trackers"):
        return Recommendation(
            "trackers",
            "Tracker changes need config parsing and track-mode focused coverage.",
            pytest=("pytest tests/test_python.py::test_track_stream", "pytest tests/test_solutions.py::test_solution"),
            notes=("Track-stream and solution tests can require online media or optional solution assets.",),
            extras=("solutions",),
        )

    if has_prefix(path, "ultralytics/cfg/datasets"):
        return Recommendation(
            "dataset config",
            "Dataset YAML changes need config validation before training or validation smoke.",
            pytest=("pytest tests/test_python.py::test_cfg_init",),
            cli=("yolo cfg",),
            notes=("Training/validation tests may download datasets; keep them opt-in.",),
        )

    if path == "ultralytics/cfg/default.yaml" or has_prefix(path, "ultralytics/cfg"):
        return Recommendation(
            "configuration and cli",
            "Default config or CLI parser changes should preserve special modes and config rendering.",
            pytest=("pytest tests/test_cli.py::test_special_modes", "pytest tests/test_python.py::test_cfg_init"),
            cli=("yolo --help", "yolo version", "yolo cfg"),
        )

    if has_prefix(path, "ultralytics/solutions"):
        return Recommendation(
            "solutions",
            "Solution changes need targeted solution class tests and optional dependency awareness.",
            pytest=(
                "pytest tests/test_solutions.py::test_config_update_method_with_invalid_argument",
                "pytest tests/test_solutions.py::test_solution",
            ),
            notes=("Similarity search, Streamlit, and video assets require solutions extras and may be expensive.",),
            extras=("solutions",),
        )

    if has_prefix(path, "ultralytics/nn/backends"):
        return Recommendation(
            "deployment backends",
            "Backend adapter changes need export environment registration and targeted backend tests.",
            pytest=("pytest tests/test_exports.py::test_export_env_has_smoke",),
            notes=("Route runtime/export setup details to the export-and-deployment sub-skill.",),
            extras=("export-base or backend-specific export extra",),
        )

    if has_prefix(path, "ultralytics/nn", "ultralytics/models"):
        return Recommendation(
            "models and nn",
            "Model-family or network changes need construction and API smoke coverage.",
            pytest=("pytest tests/test_engine.py::test_task", "pytest tests/test_python.py::test_all_model_yamls"),
            notes=("Parametrized task/model tests can download weights; confirm assets are cached first.",),
        )

    if has_prefix(path, "ultralytics/utils"):
        return Recommendation(
            "utils",
            "Shared utility changes should run named utility tests before integrations.",
            pytest=("pytest tests/test_python.py::test_utils_init", "pytest tests/test_python.py::test_utils_checks"),
            notes=("Choose a more specific utility test when the edited helper has direct coverage.",),
        )

    return Recommendation(
        "general",
        "No specific mapping matched; start with CLI smoke and inspect nearby tests.",
        pytest=("pytest tests/test_cli.py::test_special_modes",),
        cli=("yolo --help", "yolo version"),
        notes=("Add subsystem-specific tests after identifying the touched runtime area.",),
    )


def append_unique(target: list[str], values: Iterable[str]) -> None:
    """Append values while preserving first-seen order."""

    for value in values:
        if value and value not in target:
            target.append(value)


def build_plan(paths: Iterable[str]) -> Plan:
    """Build a combined recommendation plan for changed paths."""

    plan = Plan()
    normalized_paths = [normalize_path(path) for path in paths if normalize_path(path)] or [""]

    for path in normalized_paths:
        recommendation = recommendation_for(path)
        append_unique(plan.categories, (recommendation.category,))
        append_unique(plan.pytest, recommendation.pytest)
        append_unique(plan.cli, recommendation.cli)
        append_unique(plan.extras, recommendation.extras)
        append_unique(plan.notes, (f"{path or '<unspecified>'}: {recommendation.reason}", *recommendation.notes))

    if any("test_cuda.py" in command or " --slow" in command for command in plan.pytest):
        append_unique(plan.notes, ("CUDA and --slow commands are environment-gated, not default smoke checks.",))

    return plan


def print_text(plan: Plan) -> None:
    """Print a human-readable plan."""

    print("Focused Ultralytics maintainer check plan")
    print("Categories: " + ", ".join(plan.categories))

    if plan.pytest:
        print("\nPytest candidates:")
        for command in plan.pytest:
            print(f"  - {command}")

    if plan.cli:
        print("\nSafe CLI/doc commands to consider:")
        for command in plan.cli:
            print(f"  - {command}")

    if plan.extras:
        print("\nOptional extras likely needed:")
        for extra in plan.extras:
            print(f"  - {extra}")

    if plan.notes:
        print("\nNotes:")
        for note in plan.notes:
            print(f"  - {note}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Suggest focused Ultralytics maintainer checks for changed repository paths without running them."
    )
    parser.add_argument("paths", nargs="*", help="Changed repository paths, such as ultralytics/engine/results.py")
    parser.add_argument("--json", action="store_true", help="Print the plan as JSON for automation")
    return parser.parse_args()


def main() -> None:
    """Run the focused-check planner."""

    args = parse_args()
    plan = build_plan(args.paths)
    payload = {
        "categories": plan.categories,
        "pytest": plan.pytest,
        "cli": plan.cli,
        "extras": plan.extras,
        "notes": plan.notes,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print_text(plan)


if __name__ == "__main__":
    main()
