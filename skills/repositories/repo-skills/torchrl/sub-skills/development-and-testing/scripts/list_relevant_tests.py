#!/usr/bin/env python3
"""Suggest focused TorchRL tests and CI concerns from touched paths.

The script is intentionally standalone: it only uses path strings supplied on the
command line or through an explicitly supplied file list. It does not require a
TorchRL checkout unless the caller passes paths from one.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Rule:
    """Mapping from touched path fragments to test and CI suggestions."""

    name: str
    fragments: tuple[str, ...]
    tests: tuple[str, ...]
    notes: tuple[str, ...] = ()
    labels: tuple[str, ...] = ()


@dataclass
class SuggestionSet:
    """Accumulated suggestions for one invocation."""

    categories: set[str] = field(default_factory=set)
    tests: set[str] = field(default_factory=set)
    notes: set[str] = field(default_factory=set)
    labels: set[str] = field(default_factory=set)
    unmatched: list[str] = field(default_factory=list)


RULES: tuple[Rule, ...] = (
    Rule(
        name="envs",
        fragments=("torchrl/envs/", "test/envs/"),
        tests=(
            "test/envs/test_env_base.py",
            "test/envs/test_step_mdp.py",
            "test/transforms/ relevant transform selector",
        ),
        notes=(
            "Check specs, reset/rollout behavior, done/truncated layout, process-start behavior, and nested keys.",
        ),
    ),
    Rule(
        name="transforms",
        fragments=("torchrl/envs/transforms/", "test/transforms/"),
        tests=(
            "test/transforms/",
            "test/envs/test_step_mdp.py when next-state layout changes",
        ),
        notes=(
            "If transform keys accept NestedKey, include a nested-key test.",
            "Hot key transforms should avoid data-dependent shapes and Python branches on tensor values.",
        ),
    ),
    Rule(
        name="collectors",
        fragments=("torchrl/collectors/", "test/collectors/", "test/test_collectors.py"),
        tests=(
            "test/test_collectors.py or the touched collector test file",
            "test/collectors/test_evaluator.py for evaluator changes",
        ),
        notes=(
            "Collector tests often spawn processes and may need serial reproduction rather than xdist.",
            "Check device, storing_device, policy_device, and env_device behavior when data movement changes.",
        ),
    ),
    Rule(
        name="replay-buffers",
        fragments=("torchrl/data/replay_buffers/", "test/rb/"),
        tests=(
            "test/rb/test_rb_core.py",
            "test/rb/test_prioritized.py for priority changes",
            "storage/sampler-specific test/rb file when touched",
        ),
        notes=(
            "Check sample units, returned TensorDict shape, priority updates, memmap cleanup, and device placement.",
        ),
    ),
    Rule(
        name="modules-policies",
        fragments=("torchrl/modules/", "test/modules/"),
        tests=(
            "test/modules/test_actor.py",
            "test/modules/test_rnn.py for recurrent changes",
            "test/modules/test_multiagent_models.py for multi-agent changes",
        ),
        notes=(
            "Check in_keys/out_keys, TensorDict specs, distribution parameter shapes, recurrent primers, and nested keys.",
        ),
    ),
    Rule(
        name="objectives",
        fragments=("torchrl/objectives/", "test/objectives/"),
        tests=(
            "matching test/objectives/test_<algorithm>.py",
            "related module/replay tests when loss inputs or weights change",
        ),
        notes=(
            "Check _AcceptedKeys, set_keys(), value estimator keys, target updater cadence, and nested-key behavior.",
        ),
    ),
    Rule(
        name="trainer-configs",
        fragments=("torchrl/trainers/", "test/test_configs.py"),
        tests=(
            "test/test_configs.py",
            "matching algorithm/objective tests for runtime behavior",
        ),
        notes=(
            "For classes with Hydra companions, keep constructor kwargs, Config fields, defaults, _make_* forwarding, docs, and tests in parity.",
        ),
    ),
    Rule(
        name="services",
        fragments=("torchrl/services/", "test/services/", "test/test_inference_server.py"),
        tests=(
            "test/services/",
            "test/test_inference_server.py when inference server behavior changes",
        ),
        notes=(
            "Service tests can spawn processes or require Ray; reproduce serially when diagnosing flakes.",
        ),
        labels=("ci/optdeps when optional service backends or import paths change",),
    ),
    Rule(
        name="llm-vla",
        fragments=(
            "torchrl/envs/llm/",
            "torchrl/modules/llm/",
            "torchrl/collectors/llm/",
            "torchrl/objectives/llm/",
            "torchrl/data/llm/",
            "torchrl/data/vla/",
            "torchrl/modules/vla/",
            "test/llm/",
            "test/data/test_vla.py",
            "test/objectives/test_vla.py",
        ),
        tests=(
            "test/data/test_vla.py for VLA schema/data changes",
            "test/objectives/test_vla.py for VLA objective changes",
            "test/llm/ when LLM dependencies are provisioned",
        ),
        notes=(
            "Separate CPU-verifiable schema tests from model download, GPU serving, or external-service tests.",
        ),
        labels=("ci/optdeps for optional LLM/VLA integration or import-path changes",),
    ),
    Rule(
        name="docs-reference",
        fragments=("docs/source/reference/",),
        tests=(
            "docs build or repository doc checker scripts when available",
            "runtime tests for any documented behavior change",
        ),
        notes=(
            "New public classes/functions need reference entries and runnable docstring examples when practical.",
        ),
    ),
    Rule(
        name="tutorials",
        fragments=("tutorials/",),
        tests=(
            "matching tutorial smoke or docs build when available",
            "unit tests for API behavior shown in the tutorial",
        ),
        notes=(
            "Tutorials should be Sphinx-first with prose comments, conclusion/further-reading sections, and clear optional dependency gates.",
        ),
    ),
    Rule(
        name="benchmarks",
        fragments=("benchmarks/",),
        tests=(
            "matching benchmark file",
            "focused correctness tests for the same hot path",
        ),
        notes=(
            "Benchmarks supplement correctness tests; they do not replace unit coverage.",
        ),
    ),
    Rule(
        name="sota",
        fragments=("sota-implementations/", "sota-check/", ".github/unittest/linux_sota/"),
        tests=(
            "SOTA smoke list for the changed algorithm",
            "unit tests for algorithm wiring and configs",
        ),
        notes=(
            "New algorithms need SOTA script/config/check entries in addition to ordinary unit tests.",
        ),
    ),
    Rule(
        name="ci-config",
        fragments=(".github/workflows/", ".github/unittest/", "pytest.ini"),
        tests=(
            "affected CI helper script in a dry-run or narrow local reproduction",
            "pytest collection command for changed marker behavior",
        ),
        notes=(
            "Check CPU/GPU marker filtering, process-spawning quarantine, xdist behavior, and PR-gated labels.",
        ),
    ),
    Rule(
        name="packaging",
        fragments=("pyproject.toml", "setup.py", "setup.cfg", "version.txt", "MANIFEST.in"),
        tests=(
            "test/smoke_test.py",
            "test/smoke_test_deps.py when dependency declarations change",
            "editable install plus pip check in the target environment",
        ),
        notes=(
            "Dependency or packaging changes can affect import smoke and optional extras.",
        ),
        labels=("ci/optdeps when optional extras or optional imports change",),
    ),
)

DEFAULT_NOTES: tuple[str, ...] = (
    "Run direct tests covering changed behavior before expanding to broader suites.",
    "Add ci/olddeps if the change uses a torch API or behavior that may not exist in the oldest supported stack.",
    "Run check_gpu_marker_policy.py on changed tests when CUDA, Triton, or device-count skip conditions appear.",
)


def _normalize_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _read_path_list(files: Iterable[Path]) -> list[str]:
    paths: list[str] = []
    for file_path in files:
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise SystemExit(f"could not read path list {file_path}: {exc}") from exc
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                paths.append(stripped)
    return paths


def _matches(path: str, fragment: str) -> bool:
    return path == fragment or fragment in path or path.endswith(fragment)


def build_suggestions(paths: Iterable[str]) -> SuggestionSet:
    suggestions = SuggestionSet()
    normalized_paths = [_normalize_path(path) for path in paths if path.strip()]

    for path in normalized_paths:
        matched = False
        for rule in RULES:
            if any(_matches(path, fragment) for fragment in rule.fragments):
                matched = True
                suggestions.categories.add(rule.name)
                suggestions.tests.update(rule.tests)
                suggestions.notes.update(rule.notes)
                suggestions.labels.update(rule.labels)
        if not matched:
            suggestions.unmatched.append(path)

    suggestions.notes.update(DEFAULT_NOTES)
    return suggestions


def _as_json(suggestions: SuggestionSet) -> str:
    payload = {
        "categories": sorted(suggestions.categories),
        "tests": sorted(suggestions.tests),
        "ci_labels_or_attention": sorted(suggestions.labels),
        "notes": sorted(suggestions.notes),
        "unmatched_paths": suggestions.unmatched,
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def _print_section(title: str, items: Iterable[str]) -> None:
    materialized = list(items)
    if not materialized:
        return
    print(f"\n{title}")
    print("-" * len(title))
    for item in materialized:
        print(f"- {item}")


def _print_text(suggestions: SuggestionSet) -> None:
    if suggestions.categories:
        _print_section("Matched categories", sorted(suggestions.categories))
    else:
        print("No known TorchRL area matched the supplied paths.")
    _print_section("Suggested test targets", sorted(suggestions.tests))
    _print_section("CI labels or attention", sorted(suggestions.labels))
    _print_section("Notes", sorted(suggestions.notes))
    _print_section("Unmatched paths", suggestions.unmatched)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Suggest focused TorchRL tests and CI concerns from touched paths."
    )
    parser.add_argument("paths", nargs="*", help="Touched file or directory paths.")
    parser.add_argument(
        "--from-file",
        action="append",
        type=Path,
        default=[],
        help="Read additional touched paths from a newline-delimited file.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    paths = list(args.paths)
    paths.extend(_read_path_list(args.from_file))

    if not paths:
        print("No paths supplied. Pass changed files or --from-file.", file=sys.stderr)
        return 2

    suggestions = build_suggestions(paths)
    if args.json:
        print(_as_json(suggestions))
    else:
        _print_text(suggestions)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
