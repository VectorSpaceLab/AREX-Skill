#!/usr/bin/env python3
"""Select a minimal Marqo test plan from changed paths.

Default behavior is print-only. Pass --run to execute only safe CPU unit-test
commands; service-backed integration/API tests are never executed by this script.
"""

from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent


@dataclass(frozen=True)
class Command:
    key: str
    title: str
    cwd: str
    command: tuple[str, ...]
    safety: str = "safe-unit"
    service: bool = False

    def shell(self) -> str:
        joined = " ".join(self.command)
        return f"cd {self.cwd} && {joined}"


COMMANDS: dict[str, Command] = {
    "marqo_index": Command(
        key="marqo_index",
        title="Marqo index model unit tests",
        cwd="components/marqo",
        command=("env", "PYTHONPATH=./src", "pytest", "tests/unit_tests/marqo/core/models/test_marqo_index.py", "-q"),
    ),
    "semi_structured_core": Command(
        key="semi_structured_core",
        title="Semi-structured Vespa index core unit tests",
        cwd="components/marqo",
        command=(
            "env", "PYTHONPATH=./src", "pytest",
            "tests/unit_tests/marqo/core/semi_structured_vespa_index/test_semi_structured_vespa_index.py",
            "tests/unit_tests/marqo/core/semi_structured_vespa_index/test_semi_structured_add_document_handler.py",
            "tests/unit_tests/marqo/core/semi_structured_vespa_index/test_semi_structured_document.py",
            "tests/unit_tests/marqo/core/semi_structured_vespa_index/test_semi_structured_vespa_index_to_vespa_query.py",
            "tests/unit_tests/marqo/core/semi_structured_vespa_index/test_semi_structured_vespa_index_in_filter.py",
            "-q",
        ),
    ),
    "api_validation": Command(
        key="api_validation",
        title="API route and validation unit tests",
        cwd="components/marqo",
        command=(
            "env", "PYTHONPATH=./src", "pytest",
            "tests/unit_tests/marqo/tensor_search/test_validation.py",
            "tests/unit_tests/marqo/tensor_search/test_api.py",
            "tests/unit_tests/marqo/tensor_search/test_api_typeahead.py",
            "-q",
        ),
    ),
    "search_filter": Command(
        key="search_filter",
        title="Search/filter/hybrid unit tests",
        cwd="components/marqo",
        command=(
            "env", "PYTHONPATH=./src", "pytest",
            "tests/unit_tests/marqo/core/search/test_hybrid_search.py",
            "tests/unit_tests/marqo/core/search/test_search_filter.py",
            "-q",
        ),
    ),
    "maven_build": Command(
        key="maven_build",
        title="Vespa custom searcher Maven build",
        cwd="components/marqo/vespa",
        command=("mvn", "clean", "package"),
        safety="build-only",
    ),
    "inference_unit": Command(
        key="inference_unit",
        title="Inference orchestrator safe unit tests",
        cwd="components/inference_orchestrator",
        command=(
            "env", "PYTHONPATH=./src", "pytest",
            "tests/unit_tests/services/media_download_and_preprocess/test_split_text.py",
            "tests/unit_tests/services/triton_inference/inference_pipelines/test_random_model_inference_pipeline.py",
            "-q",
        ),
    ),
    "model_mgmt_unit": Command(
        key="model_mgmt_unit",
        title="Model-management safe unit tests",
        cwd="components/model_management",
        command=(
            "env", "PYTHONPATH=./src", "pytest",
            "tests/unit_tests/schemas/test_triton_model_properties.py",
            "tests/unit_tests/service/model_manager/test_url_parser.py",
            "-q",
        ),
    ),
    "semi_structured_service": Command(
        key="semi_structured_service",
        title="Optional Vespa-backed semi-structured integration tests",
        cwd="components/marqo",
        command=(
            "env", "PYTHONPATH=./src", "pytest",
            "tests/integ_tests/core/semi_structured_vespa_index/test_semi_structured_vespa_index.py",
            "tests/integ_tests/core/semi_structured_vespa_index/test_semi_structured_vespa_schema.py",
            "tests/integ_tests/tensor_search/integ_tests/test_search_semi_structured.py",
            "-q",
        ),
        safety="service-backed; requires Vespa/API config",
        service=True,
    ),
    "api_service": Command(
        key="api_service",
        title="Optional API service tests",
        cwd="components/marqo",
        command=(
            "env", "PYTHONPATH=./tests/api_tests/v1/tests/api_tests", "pytest",
            "tests/api_tests/v1/tests/api_tests/test_health.py",
            "tests/api_tests/v1/tests/api_tests/test_create_index.py",
            "-q",
        ),
        safety="service-backed; requires local Marqo API and Vespa; mutates indexes",
        service=True,
    ),
}

ORDER = [
    "marqo_index",
    "semi_structured_core",
    "api_validation",
    "search_filter",
    "maven_build",
    "inference_unit",
    "model_mgmt_unit",
    "semi_structured_service",
    "api_service",
]


def changed_from_git() -> list[str]:
    names: set[str] = set()
    for args in (["git", "diff", "--name-only"], ["git", "diff", "--name-only", "--cached"]):
        try:
            output = subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.CalledProcessError):
            continue
        names.update(line.strip() for line in output.splitlines() if line.strip())
    return sorted(names)


def select_keys(paths: list[str]) -> set[str]:
    if not paths:
        return {"marqo_index", "api_validation", "inference_unit", "model_mgmt_unit"}

    keys: set[str] = set()
    for raw in paths:
        path = raw.replace("\\", "/")
        if "components/marqo/src/marqo/core/semi_structured_vespa_index/" in path:
            keys.update({"marqo_index", "semi_structured_core", "semi_structured_service"})
        if "components/marqo/src/marqo/core/structured_vespa_index/" in path:
            keys.update({"marqo_index", "semi_structured_core"})
        if "components/marqo/src/marqo/core/models/" in path or "marqo_index" in path:
            keys.add("marqo_index")
        if "components/marqo/src/marqo/tensor_search/" in path or "components/marqo/src/marqo/api/" in path:
            keys.update({"api_validation", "api_service"})
        if "components/marqo/tests/api_tests/" in path:
            keys.add("api_service")
        if "components/marqo/src/marqo/core/search/" in path:
            keys.add("search_filter")
        if "components/marqo/vespa/" in path:
            keys.add("maven_build")
            if path.endswith("HybridSearcher.java"):
                keys.update({"search_filter", "semi_structured_service"})
        if "components/inference_orchestrator/" in path:
            keys.add("inference_unit")
        if "components/model_management/" in path:
            keys.add("model_mgmt_unit")
        if any(token in path for token in ["compose.yaml", "compose-inference.yaml", "compose-model-management.yaml", "compose-triton.yaml", "Dockerfile", ".env", "run_marqo.sh"]):
            # Do not select container-mutating tests by default; emit a service lifecycle reminder via API service plan.
            keys.add("api_service")
    return keys


def find_repo_root(start: Path) -> Path | None:
    for path in [start, *start.parents]:
        if (path / "components" / "marqo").is_dir() and (path / "compose.yaml").is_file():
            return path
    return None


def render(commands: list[Command]) -> str:
    blocks = []
    for cmd in commands:
        blocks.append(dedent(f"""
        # {cmd.title}
        # Safety: {cmd.safety}
        {cmd.shell()}
        """).strip())
    return "\n\n".join(blocks)


def run_commands(commands: list[Command], repo_root: Path) -> int:
    for cmd in commands:
        if cmd.service:
            print(f"SKIP service-backed command: {cmd.key} ({cmd.safety})")
            continue
        if cmd.key == "maven_build":
            print("SKIP build command by default: maven_build. Run the printed Maven command manually after review.")
            continue
        cwd = repo_root / cmd.cwd
        print(f"RUN {cmd.key}: {cmd.shell()}")
        completed = subprocess.run(cmd.command, cwd=cwd)
        if completed.returncode != 0:
            return completed.returncode
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Changed file paths to classify.")
    parser.add_argument("--from-git", action="store_true", help="Use git diff --name-only plus cached changes as input paths.")
    parser.add_argument("--include-service", action="store_true", help="Print service-backed integration/API test plans too.")
    parser.add_argument("--run", action="store_true", help="Execute selected safe CPU unit-test commands only. Never runs service-backed tests.")
    args = parser.parse_args()

    paths = list(args.paths)
    if args.from_git:
        paths.extend(changed_from_git())

    keys = select_keys(paths)
    commands = [COMMANDS[key] for key in ORDER if key in keys and (args.include_service or not COMMANDS[key].service)]
    service_skipped = [COMMANDS[key] for key in ORDER if key in keys and COMMANDS[key].service and not args.include_service]

    print("# DRY RUN by default: selected commands are printed only.")
    if paths:
        print("# Classified paths:")
        for path in paths:
            print(f"# - {path}")
    else:
        print("# No paths supplied; printing a small cross-component smoke unit plan.")

    if commands:
        print(render(commands))
    else:
        print("# No safe unit commands selected. Inspect the changed paths manually.")

    if service_skipped:
        print("\n# Service-backed plans omitted. Re-run with --include-service to print them:")
        for cmd in service_skipped:
            print(f"# - {cmd.key}: {cmd.title} ({cmd.safety})")

    if not args.run:
        return 0

    repo_root = find_repo_root(Path.cwd())
    if repo_root is None:
        print("ERROR: cannot locate repository root; refusing to run commands.")
        return 2
    runnable = [cmd for cmd in commands if not cmd.service]
    return run_commands(runnable, repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
