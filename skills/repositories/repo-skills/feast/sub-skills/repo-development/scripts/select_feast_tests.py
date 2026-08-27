#!/usr/bin/env python3
"""Suggest scoped Feast development checks from changed paths.

This helper is advisory only: it prints commands and never executes tests,
linters, formatters, package installs, network calls, or service checks.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import sys
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Iterable


@dataclass(frozen=True)
class Suggestion:
    command: str
    reason: str
    safety: str = "safe-local"


@dataclass
class SuggestionSet:
    suggestions: list[Suggestion] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    seen_commands: set[str] = field(default_factory=set)

    def add(self, command: str, reason: str, safety: str = "safe-local") -> None:
        if command not in self.seen_commands:
            self.suggestions.append(Suggestion(command=command, reason=reason, safety=safety))
            self.seen_commands.add(command)

    def note(self, message: str) -> None:
        if message not in self.notes:
            self.notes.append(message)


def normalize_path(path: str) -> str:
    return str(PurePosixPath(path.replace("\\", "/"))).lstrip("./")


def python_module_for_mypy(path: str) -> str | None:
    prefix = "sdk/python/"
    feast_prefix = "sdk/python/feast/"
    if not path.startswith(feast_prefix) or not path.endswith(".py"):
        return None
    return path.removeprefix(prefix)


def add_python_file_checks(result: SuggestionSet, paths: list[str]) -> None:
    python_paths = [path for path in paths if path.startswith(("sdk/python/feast/", "sdk/python/tests/")) and path.endswith(".py")]
    if not python_paths:
        return

    joined = " ".join(python_paths)
    result.add(f"uv run ruff check {joined}", "Lint changed Python implementation/test files.")
    result.add(f"uv run ruff format {joined}", "Format changed Python implementation/test files.")

    mypy_targets = [python_module_for_mypy(path) for path in python_paths]
    mypy_targets = [target for target in mypy_targets if target]
    if mypy_targets:
        result.add(
            f"uv run bash -c \"cd sdk/python && mypy {' '.join(mypy_targets)}\"",
            "Type-check changed Feast package modules from sdk/python.",
        )


def suggest_for_path(result: SuggestionSet, path: str) -> None:
    if path == "AGENTS.md" or path == "Makefile" or path.startswith("infra/scripts/pixi/") or path in {"pyproject.toml", "sdk/python/pyproject.toml"}:
        result.add("make help", "Inspect available Makefile targets after workflow/dependency changes.")
        result.add("make test-python-smoke", "Run the quick Python smoke target after contributor workflow changes.")
        result.note("Dependency or workflow changes may require a fresh dev install before broad validation.")

    if path.startswith("sdk/python/feast/feature_store.py"):
        result.add(
            "uv run python -m pytest sdk/python/tests/unit/test_unit_feature_store.py -k \"apply or registry or plan\" -v",
            "Exercise core FeatureStore apply, registry, and plan behavior.",
        )
        result.add(
            "uv run python -m pytest sdk/python/tests/unit/infra/registry/ -v",
            "Check registry behavior affected by FeatureStore changes.",
        )
        result.add("make test-python-smoke", "Add quick core smoke coverage.")

    if path.startswith("sdk/python/feast/infra/registry/"):
        result.add("uv run python -m pytest sdk/python/tests/unit/infra/registry/ -v", "Run registry unit tests.")
        result.add("make test-python-smoke", "Add smoke coverage for registry/apply interactions.")

    if path.startswith("sdk/python/feast/repo_config.py") or "repo_config" in path:
        result.add(
            "uv run python -m pytest sdk/python/tests/unit -k \"repo_config or feature_store_yaml or project_name\" -v",
            "Focus config parsing and project validation tests.",
        )

    if path.startswith("sdk/python/feast/cli/"):
        result.add("uv run python -m pytest sdk/python/tests/unit -k \"cli or init or apply or plan\" -v", "Run CLI-related unit coverage.")
        result.add("uv run feast --help", "Verify the Feast CLI entry point imports and lists commands.")

    if path.startswith("sdk/python/feast/infra/online_stores/"):
        store_name = PurePosixPath(path).stem.replace("_online_store", "")
        result.add("uv run python -m pytest sdk/python/tests/unit/infra/online_store/ -v", "Run online store unit tests.")
        if store_name:
            result.add(
                f"uv run python -m pytest sdk/python/tests/unit/infra/online_store/ -k \"{store_name}\" -v",
                "Try a store-name filter if matching tests exist.",
            )
        result.note("Service-backed online store integration tests require explicit prerequisites and should be skipped by default.")

    if path.startswith("sdk/python/feast/infra/offline_stores/"):
        store_name = PurePosixPath(path).stem.replace("_offline_store", "")
        result.add("uv run python -m pytest sdk/python/tests/unit -k \"offline_store or data_source or retrieval\" -v", "Run offline store and retrieval-adjacent unit coverage.")
        if store_name:
            result.add(
                f"uv run python -m pytest sdk/python/tests/unit -k \"{store_name}\" -v",
                "Try a store-name filter if matching tests exist.",
            )
        result.note("Cloud-backed offline store integration tests require credentials and should be skipped unless authorized.")

    if "feature_server" in path or path.startswith("sdk/python/feast/infra/feature_servers/"):
        result.add("uv run python -m pytest sdk/python/tests/unit -k \"feature_server or server\" -v", "Run feature server unit coverage.")
        result.note("Route serving topology, TLS, and auth behavior to the servers-and-remote sub-skill.")

    if path.startswith("sdk/python/feast/permissions/") or "rbac" in path.lower():
        result.add("uv run python -m pytest sdk/python/tests/unit -k \"permission or rbac or auth\" -v", "Run permission/RBAC unit coverage.")
        result.note("Remote RBAC integration tests are unsafe without explicit service prerequisites.")

    if path.startswith("sdk/python/tests/unit/") and path.endswith(".py"):
        result.add(f"uv run python -m pytest {path} -v", "Run the changed unit test file directly.")

    if path.startswith("sdk/python/tests/integration/") and path.endswith(".py"):
        result.add(
            f"uv run python -m pytest --integration {path} -v --tb=short",
            "Run the changed integration test only if its services are available.",
            safety="requires-prereqs",
        )
        result.note("Do not run integration tests that need cloud credentials, Docker, or external services unless explicitly authorized.")

    if path.startswith("protos/") or path.endswith(".proto"):
        result.add("make compile-protos-python", "Regenerate Python protobuf outputs.")
        result.add("make protos", "Regenerate Python protobufs and proto docs.")
        result.add("make compile-protos-go", "Regenerate Go protobuf outputs if Go serving APIs are affected.")
        result.note("Run Go/Java checks when shared serving APIs changed.")

    if path.startswith("go/"):
        result.add("make format-go", "Format Go code.")
        result.add("make lint-go", "Run Go vet target after proto generation.")
        result.add("make build-go", "Build Go feature server.")
        result.add("make test-go", "Run Go tests when dependencies are available.", safety="may-install-local-deps")

    if path.startswith("java/"):
        result.add("make format-java", "Format Java code with Maven Spotless.")
        result.add("make lint-java", "Check Java formatting/lint.")
        result.add("make test-java", "Run Java unit tests.")
        result.add("make build-java", "Run full Java build when needed.", safety="heavier-local")

    if path.startswith("docs/"):
        result.add("make build-templates", "Regenerate/check documentation templates when docs navigation or templates changed.")
        result.note("Normal docs belong under docs/ and should be linked from navigation.")

    if path.startswith("infra/website/docs/blog/"):
        result.note("Blog posts must include title, description, date, and authors frontmatter.")

    if path.startswith("infra/feast-operator/"):
        result.note("Operator checks may require Docker or Kubernetes tooling; run operator-local targets only when prerequisites are available.")

    if path.startswith("ui/"):
        result.note("UI checks require Node/Yarn tooling and are outside the default Python validation path.")


def feast_version_note(require_feast: bool) -> str | None:
    try:
        version = importlib.metadata.version("feast")
    except importlib.metadata.PackageNotFoundError:
        if require_feast:
            raise SystemExit(
                "Feast is not installed in this Python environment. Install the package or omit --require-feast; "
                "this helper can suggest commands without Feast installed."
            )
        return "Feast package not detected; suggestions are still generated because no commands are executed."
    return f"Detected installed Feast distribution: {version}."


def build_suggestions(paths: Iterable[str]) -> SuggestionSet:
    normalized_paths = [normalize_path(path) for path in paths]
    result = SuggestionSet()
    add_python_file_checks(result, normalized_paths)
    for path in normalized_paths:
        suggest_for_path(result, path)

    if not result.suggestions:
        result.add("git diff --name-only", "Inspect changed files and choose the nearest scoped checks.")
        result.add("make test-python-smoke", "Fallback quick smoke for uncertain Python-facing changes.")
        result.note("No Feast-specific path heuristic matched; review neighboring tests before broad suites.")

    return result


def print_text(result: SuggestionSet, version_note: str | None) -> None:
    if version_note:
        print(version_note)
    print("\nSuggested scoped commands (not executed):")
    for index, suggestion in enumerate(result.suggestions, start=1):
        print(f"{index}. {suggestion.command}")
        print(f"   reason: {suggestion.reason}")
        print(f"   safety: {suggestion.safety}")
    if result.notes:
        print("\nNotes:")
        for note in result.notes:
            print(f"- {note}")


def print_json(result: SuggestionSet, version_note: str | None) -> None:
    import json

    payload = {
        "version_note": version_note,
        "suggestions": [suggestion.__dict__ for suggestion in result.suggestions],
        "notes": result.notes,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Suggest small, safe Feast repo-development checks from changed paths. Commands are printed only; nothing is executed.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Changed Feast repository paths, for example sdk/python/feast/feature_store.py or protos/feast/core/Feature.proto.",
    )
    parser.add_argument(
        "--from-stdin",
        action="store_true",
        help="Read additional newline-delimited paths from stdin.",
    )
    parser.add_argument(
        "--require-feast",
        action="store_true",
        help="Fail if the Feast Python distribution is not installed. By default the script only notes whether it is installed.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human-readable text.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    paths = list(args.paths)
    if args.from_stdin:
        paths.extend(line.strip() for line in sys.stdin if line.strip())
    if not paths:
        raise SystemExit("Provide at least one changed path or use --from-stdin. Try --help for examples.")

    version_note = feast_version_note(require_feast=args.require_feast)
    result = build_suggestions(paths)
    if args.json:
        print_json(result, version_note)
    else:
        print_text(result, version_note)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
