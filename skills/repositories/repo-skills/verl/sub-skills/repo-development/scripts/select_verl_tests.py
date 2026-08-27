#!/usr/bin/env python3
"""Suggest focused verl tests and pre-commit hooks for changed paths.

This helper is intentionally read-only: it prints suggestions and never invokes
pytest, pre-commit, git, GitHub, or repository mutating scripts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import PurePosixPath
from typing import Iterable


def normalize_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def add_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def area_from_verl_path(path: str) -> str | None:
    parts = PurePosixPath(path).parts
    if len(parts) < 2 or parts[0] != "verl":
        return None
    return parts[1]


def suggest_for_paths(paths: Iterable[str]) -> dict[str, object]:
    normalized_paths = [p for p in (normalize_path(path) for path in paths) if p]
    tests: list[str] = []
    hooks: list[str] = []
    notes: list[str] = []
    warnings: list[str] = []

    add_unique(hooks, "ruff")
    add_unique(hooks, "ruff-format")

    touched_tests = False
    touched_config = False
    touched_docs = False
    touched_agent_instructions = False
    touched_workflows = False
    touched_examples = False
    touched_npu = False
    touched_gpu_or_distributed = False

    for path in normalized_paths:
        parts = PurePosixPath(path).parts
        suffix = PurePosixPath(path).suffix

        if path in {"AGENTS.md", "CLAUDE.md"} or path.startswith((".agent/", ".codex/", ".claude/")):
            touched_agent_instructions = True
        if path.startswith("docs/contributing/") and "agent" in PurePosixPath(path).name:
            touched_agent_instructions = True
        if path.startswith("docs/") or path == "CONTRIBUTING.md":
            touched_docs = True
        if path.startswith(".github/workflows/"):
            touched_workflows = True
        if path.startswith("examples/"):
            touched_examples = True
        if path.startswith("tests/"):
            touched_tests = True
            add_unique(tests, f"pytest {path}" if path.endswith(".py") else f"pytest {path}")
        if path.startswith("tests/special_npu/") or "_on_npu" in path or "ascend" in path.lower() or "npu" in path.lower():
            touched_npu = True
        if path.startswith("tests/special_distributed/") or "_on_gpu" in path or any(token in path.lower() for token in ("vllm", "sglang", "megatron", "fsdp")):
            touched_gpu_or_distributed = True
        if path.startswith("verl/trainer/config/") or path.startswith("scripts/print_cfg.py") or path == "scripts/generate_trainer_config.sh":
            touched_config = True
        if path.startswith("verl/") and suffix == ".py":
            area = area_from_verl_path(path)
            if area:
                candidate = f"tests/{area}"
                add_unique(tests, f"pytest {candidate}")

    if touched_config:
        add_unique(tests, "pytest tests/special_sanity/test_config_docs.py")
        add_unique(tests, "pytest tests/test_base_config_on_cpu.py")
        add_unique(hooks, "autogen-trainer-cfg")
        add_unique(notes, "Trainer generated YAML is maintained by the repo generation script/hook; inspect and commit generated diffs intentionally.")

    if touched_docs:
        add_unique(hooks, "check-docs-time-info")
        add_unique(notes, "For docs builds, install docs requirements and run the docs make targets only when the change affects rendered docs.")

    if touched_agent_instructions:
        add_unique(notes, "Read the agent-instruction editing guide before changing AGENTS.md or linked framework-specific guides.")
        add_unique(warnings, "Do not edit agent instructions unless the requested rule is non-obvious, non-duplicative, under budget, and belongs in that file.")

    if touched_workflows or touched_tests:
        add_unique(hooks, "validate-structure")
        add_unique(notes, "When adding workflow-specific tests, update path filters/exclusions so CPU/GPU broad jobs do not duplicate or miss them.")

    if touched_examples:
        add_unique(hooks, "check-example-naming")

    if any(path.endswith(".py") for path in normalized_paths):
        add_unique(hooks, "compileall")
        add_unique(tests, "pytest tests/special_sanity/test_import.py")

    if touched_npu:
        add_unique(notes, "NPU/Ascend tests require matching hardware and workflows; do not substitute GPU-only validation for NPU coverage.")
    if touched_gpu_or_distributed:
        add_unique(notes, "GPU/distributed/vLLM/SGLang/Megatron/FSDP tests may require accelerators or dedicated environments; prefer CPU mirrors when they exist for local smoke checks.")

    if not tests:
        add_unique(tests, "pytest tests/special_sanity/test_import.py")
        add_unique(notes, "No path-specific pytest target inferred; start with import smoke and choose area tests manually.")

    commands = [f"pre-commit run --all-files --show-diff-on-failure --color=always {hook}" for hook in hooks]
    pytest_commands = [test if test.startswith("pytest ") else f"pytest {test}" for test in tests]

    return {
        "changed_paths": normalized_paths,
        "pytest": pytest_commands,
        "pre_commit_hooks": hooks,
        "pre_commit_commands": commands,
        "notes": notes,
        "warnings": warnings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Suggest focused verl tests and pre-commit hooks for changed paths without executing them."
    )
    parser.add_argument("--changed-paths", nargs="*", default=[], help="Changed repository paths to classify.")
    parser.add_argument("--from-file", help="Read additional newline-separated changed paths from a file.")
    parser.add_argument("--json", action="store_true", help="Print suggestions as JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = list(args.changed_paths)
    if args.from_file:
        with open(args.from_file, encoding="utf-8") as file_obj:
            paths.extend(line.strip() for line in file_obj if line.strip())

    suggestions = suggest_for_paths(paths)
    if args.json:
        print(json.dumps(suggestions, indent=2, sort_keys=True))
        return 0

    print("Changed paths:")
    for path in suggestions["changed_paths"] or ["(none provided)"]:
        print(f"  - {path}")

    print("\nSuggested pytest commands:")
    for command in suggestions["pytest"]:
        print(f"  - {command}")

    print("\nSuggested pre-commit hooks:")
    for command in suggestions["pre_commit_commands"]:
        print(f"  - {command}")

    if suggestions["notes"]:
        print("\nNotes:")
        for note in suggestions["notes"]:
            print(f"  - {note}")

    if suggestions["warnings"]:
        print("\nWarnings:")
        for warning in suggestions["warnings"]:
            print(f"  - {warning}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
