#!/usr/bin/env python3
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""Recommend first-pass Airflow validation commands from changed paths.

This helper intentionally distills only common contribution rules. It is not a
replacement for Airflow's authoritative `breeze selective-checks` command.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import PurePosixPath


@dataclass(slots=True)
class Recommendation:
    commands: set[str] = field(default_factory=set)
    notes: set[str] = field(default_factory=set)

    def add_command(self, command: str) -> None:
        self.commands.add(command)

    def add_note(self, note: str) -> None:
        self.notes.add(note)


FULL_TEST_PATTERNS = (
    re.compile(r"^\.github/workflows/"),
    re.compile(r"^dev/breeze/src/"),
    re.compile(r"^dev/breeze/(pyproject\.toml|uv\.lock)$"),
    re.compile(r"^dev/(?!breeze/tests/).*\.py$"),
    re.compile(r"^Dockerfile"),
    re.compile(r"^scripts/ci/"),
    re.compile(r"^scripts/docker/"),
    re.compile(r"^scripts/in_container/"),
    re.compile(r"^generated/provider_dependencies\.json$"),
    re.compile(r"^airflow-core/src/airflow/api_fastapi/core_api/openapi/.*generated\.yaml$"),
    re.compile(r"^clients/gen/"),
    re.compile(r"^providers/git/src/"),
    re.compile(r"^providers/standard/src/"),
    re.compile(r"^airflow-core/tests/unit/utils/"),
    re.compile(r"^devel-common/"),
)

DOC_PATTERNS = (
    re.compile(r"^docs/"),
    re.compile(r"^airflow-core/docs/"),
    re.compile(r"^providers/.*/docs/"),
    re.compile(r"^providers-summary-docs/"),
    re.compile(r"^docker-stack-docs/"),
    re.compile(r"^chart/docs/"),
    re.compile(r"^task-sdk/docs/"),
    re.compile(r"^airflow-ctl/docs/"),
    re.compile(r"^CHANGELOG\.txt$"),
    re.compile(r"^RELEASE_NOTES\.rst$"),
)

PYTHON_SOURCE_PATTERNS = (
    re.compile(r"^airflow-core/src/.*\.py$"),
    re.compile(r"^task-sdk/src/.*\.py$"),
    re.compile(r"^airflow-ctl/src/.*\.py$"),
    re.compile(r"^providers/.*/src/.*\.py$"),
    re.compile(r"^shared/.*/src/.*\.py$"),
    re.compile(r"^scripts/.*\.py$"),
    re.compile(r"^dev/.*\.py$"),
)


def get_changed_paths(argv_paths: list[str]) -> list[str]:
    raw_paths = argv_paths or [line.strip() for line in sys.stdin if line.strip()]
    return [normalise_path(path) for path in raw_paths if path.strip()]


def normalise_path(path: str) -> str:
    path = path.strip().replace("\\", "/")
    if path.startswith("./"):
        path = path[2:]
    return path


def path_matches(path: str, patterns: Iterable[re.Pattern[str]]) -> bool:
    return any(pattern.search(path) for pattern in patterns)


def extract_provider_id(path: str) -> str | None:
    parts = PurePosixPath(path).parts
    if not parts or parts[0] != "providers" or len(parts) < 2:
        return None
    if len(parts) >= 3 and parts[1] in {"apache", "common", "microsoft"}:
        return f"{parts[1]}.{parts[2]}"
    return parts[1]


def add_project_test_for_test_file(path: str, rec: Recommendation) -> None:
    if path.startswith("airflow-core/tests/") and path.endswith(".py"):
        rec.add_command(f"uv run --project airflow-core pytest {path} -xvs")
    elif path.startswith("task-sdk/tests/") and path.endswith(".py"):
        rec.add_command(f"uv run --project task-sdk pytest {path} -xvs")
    elif path.startswith("airflow-ctl/tests/") and path.endswith(".py"):
        rec.add_command(f"uv run --project airflow-ctl pytest {path} -xvs")
    elif path.startswith("scripts/tests/") and path.endswith(".py"):
        rec.add_command(f"uv run --project scripts pytest {path} -xvs")
    elif path.startswith("providers/") and "/tests/" in path and path.endswith(".py"):
        provider = extract_provider_id(path)
        if provider:
            rec.add_command(f'breeze testing providers-tests --test-type "Providers[{provider}]"')
        rec.add_command(f"breeze run pytest {path} -xvs")


def recommend_for_path(path: str, rec: Recommendation) -> None:
    if path_matches(path, FULL_TEST_PATTERNS) or path == "pyproject.toml":
        rec.add_note(f"{path}: broad CI impact; run authoritative selective checks before PR readiness.")
        rec.add_command("breeze selective-checks --commit-ref <commit_with_squashed_changes>")
        rec.add_command("prek run --from-ref <target_branch> --stage pre-commit")

    if path_matches(path, PYTHON_SOURCE_PATTERNS):
        rec.add_command(f"uv run ruff format {path}")
        rec.add_command(f"uv run ruff check --fix {path}")

    add_project_test_for_test_file(path, rec)

    if path.startswith("airflow-core/src/airflow/api_fastapi/") or path.startswith(
        "airflow-core/tests/unit/api_fastapi/"
    ):
        rec.add_command("uv run --project airflow-core pytest airflow-core/tests/unit/api_fastapi/ -xvs")
        rec.add_note("API route/model changes may update generated OpenAPI specs through prek.")

    if path.startswith("airflow-core/src/airflow/api_fastapi/execution_api/"):
        rec.add_command("uv run --project airflow-core pytest airflow-core/tests/unit/api_fastapi/execution_api/ -xvs")
        rec.add_note("Execution API schema or behavior changes may need Cadwyn version migration tests.")

    if path.startswith("airflow-core/src/airflow/migrations/"):
        rec.add_command("prek update-migration-references --all-files")
        rec.add_note("Migration changes need upgrade/downgrade validation and no ORM imports in migration scripts.")

    if path.startswith("airflow-core/src/airflow/cli/") or path.startswith("airflow-core/tests/cli/"):
        rec.add_command("uv run --project airflow-core pytest airflow-core/tests/cli/ -xvs")

    if path.startswith("task-sdk/src/") or path.startswith("task-sdk/tests/"):
        rec.add_command("uv run --project task-sdk pytest task-sdk/tests/ -xvs")
        rec.add_command("breeze testing task-sdk-tests")

    if path.startswith("airflow-ctl/src/") or path.startswith("airflow-ctl/tests/"):
        rec.add_command("uv run --project airflow-ctl pytest airflow-ctl/tests/ -xvs")
        rec.add_command("breeze testing airflow-ctl-tests")

    if path.startswith("providers/"):
        provider = extract_provider_id(path)
        if provider:
            rec.add_command(f'uv sync --package apache-airflow-providers-{provider.replace(".", "-")}')
            rec.add_command(f'breeze testing providers-tests --test-type "Providers[{provider}]"')
        if path.endswith("pyproject.toml") or path.endswith("provider.yaml"):
            rec.add_command("prek update-providers-dependencies --all-files")
            rec.add_note(
                "Provider metadata/dependency changes may need generated dependency updates and Breeze image rebuild."
            )
        if "/docs/" in path:
            rec.add_command(f"breeze build-docs {provider or '<provider>'}")
        if "/src/" in path and path.endswith(".py"):
            rec.add_command(f"breeze run mypy {path}")
            rec.add_note("Provider code must not blindly forward Connection.extra; allowlist explicit extras.")

    if path.startswith("airflow-core/src/airflow/ui/"):
        rec.add_command("prek run ts-compile-lint-ui --all-files")
        rec.add_note(
            "UI code uses generated clients, strict TypeScript, path aliases, and no manual useMemo/useCallback."
        )

    if path.startswith("chart/"):
        rec.add_command("breeze testing helm-tests --use-xdist")
        rec.add_command("breeze build-docs helm-chart")
        rec.add_note("Chart changes may need values schema/docs updates and chart-vs-Kustomize reasoning.")

    if path_matches(path, DOC_PATTERNS):
        rec.add_command("breeze build-docs")

    if path.startswith("dev/breeze/src/airflow_breeze/utils/selective_checks.py"):
        rec.add_command("uv run --project dev/breeze pytest dev/breeze/tests/test_selective_checks.py -xvs")
        rec.add_note("Selective-check behavior changes must update selective-check docs in the same PR.")

    if path.startswith("scripts/ci/prek/"):
        rec.add_command("uv run --project scripts pytest scripts/tests/ci/prek/ -xvs")
        rec.add_note("Prek hook scripts should reuse common_prek_utils.py and register slow Breeze hooks last.")

    if path.endswith(".rst") or path.endswith(".md"):
        if "providers/" in path and "/docs/changelog.rst" in path:
            rec.add_note(
                "Provider changelog edits are for important user-visible provider changes; "
                "do not add provider newsfragments."
            )

    if "newsfragments" in path:
        rec.add_note("Newsfragments are only for user-facing changes in airflow-core, chart, or dev/mypy.")


def build_recommendations(paths: list[str]) -> Recommendation:
    rec = Recommendation()
    if not paths:
        rec.add_note("No paths supplied. Pass changed files as arguments or stdin.")
        return rec
    for path in paths:
        recommend_for_path(path, rec)
    rec.add_command("prek run --from-ref <target_branch> --stage pre-commit")
    rec.add_command("breeze selective-checks --commit-ref <commit_with_squashed_changes>")
    rec.add_note("This helper is a quick first pass; Airflow's Breeze selective checks are authoritative.")
    rec.add_note("Do not run host pytest, python, or airflow directly for repository validation.")
    return rec


def print_recommendations(paths: list[str], rec: Recommendation) -> None:
    print("Changed paths:")
    for path in paths:
        print(f"- {path}")
    print()
    print("Recommended first-pass commands:")
    for command in sorted(rec.commands):
        print(f"- {command}")
    print()
    print("Notes:")
    for note in sorted(rec.notes):
        print(f"- {note}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Changed file paths. If omitted, paths are read from stdin.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = get_changed_paths(args.paths)
    recommendations = build_recommendations(paths)
    print_recommendations(paths, recommendations)
    return 0 if paths else 2


if __name__ == "__main__":
    raise SystemExit(main())
