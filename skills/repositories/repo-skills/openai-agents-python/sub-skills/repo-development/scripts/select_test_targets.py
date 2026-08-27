#!/usr/bin/env python3
"""Suggest focused validation commands for changed openai-agents-python paths.

This helper is intentionally read-only: it prints suggested commands and never runs
formatters, tests, docs builds, snapshot tools, or service-backed checks.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Iterable


@dataclass(frozen=True)
class Suggestion:
    command: str
    reason: str
    when: str = "focused"


@dataclass
class Plan:
    changed_paths: list[str]
    suggestions: list[Suggestion] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    full_verification_recommended: bool = False
    docs_build_recommended: bool = False
    snapshot_review_recommended: bool = False
    pr_summary_recommended: bool = False

    def add(self, command: str, reason: str, when: str = "focused") -> None:
        if any(existing.command == command for existing in self.suggestions):
            return
        self.suggestions.append(Suggestion(command=command, reason=reason, when=when))

    def note(self, text: str) -> None:
        if text not in self.notes:
            self.notes.append(text)


def normalize_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return str(PurePosixPath(normalized)) if normalized else normalized


def has_prefix(path: str, *prefixes: str) -> bool:
    return any(path == prefix.rstrip("/") or path.startswith(prefix.rstrip("/") + "/") for prefix in prefixes)


def has_suffix(path: str, *suffixes: str) -> bool:
    return any(path.endswith(suffix) for suffix in suffixes)


def suggest_for_path(plan: Plan, path: str) -> None:
    if not path:
        return

    if has_prefix(path, "src/agents"):
        plan.full_verification_recommended = True
        plan.pr_summary_recommended = True
        plan.add("make format", "Runtime code changed; run formatter before final verification.", "final")
        plan.add("make lint", "Runtime code changed; lint is required by repo policy.", "final")
        plan.add("make typecheck", "Runtime code changed; typecheck is required by repo policy.", "final")
        plan.add("make tests", "Runtime code changed; full tests are required by repo policy.", "final")

    if path == "src/agents/run_state.py":
        plan.add(
            'uv run pytest -s tests/test_run_state.py -k "schema or version or roundtrip or from_json or to_json"',
            "RunState serialization changed; start with schema and round-trip tests.",
        )
        plan.add(
            'uv run pytest -s tests/test_tool_origin.py -k "legacy or run_state"',
            "RunState legacy/tool-origin payloads commonly exercise backward-read behavior.",
        )
        plan.add(
            'uv run pytest -s tests/sandbox/test_compatibility_guards.py -k "RunState or roundtrip or compatibility"',
            "Sandbox compatibility tests can cover nested serialized state.",
        )
        plan.note(
            "If serialized RunState shape changed, update CURRENT_SCHEMA_VERSION and SCHEMA_VERSION_SUMMARIES."
        )

    if path == "src/agents/run.py" or has_prefix(path, "src/agents/run_internal"):
        plan.add(
            "uv run pytest -s tests/test_agent_runner.py tests/test_agent_runner_streamed.py tests/test_run_step_execution.py tests/test_run_impl_resume_paths.py",
            "Runner or run_internal changed; cover sync, async, streamed, and resume paths.",
        )
        plan.note("Keep streaming and non-streaming behavior aligned for run loop changes.")

    if has_prefix(path, "src/agents/models") or has_prefix(path, "src/agents/extensions/models"):
        plan.add("uv run pytest -s tests/models", "Model/provider code changed; run model-provider tests.")

    if has_prefix(path, "src/agents/mcp"):
        plan.add("uv run pytest -s tests/mcp", "MCP code changed; run MCP tests.")

    if has_prefix(path, "src/agents/realtime"):
        plan.add("uv run pytest -s tests/realtime", "Realtime code changed; run realtime tests.")

    if has_prefix(path, "src/agents/voice"):
        plan.add("uv run pytest -s tests/voice", "Voice code changed; run voice tests when voice extras are installed.")
        plan.note("Voice imports require optional dependencies; record unavailable extras separately from product failures.")

    if has_prefix(path, "src/agents/sandbox") or has_prefix(path, "src/agents/extensions/sandbox"):
        plan.add("uv run pytest -s tests/sandbox", "Sandbox code changed; run sandbox tests.")
        plan.add(
            "uv run pytest -s tests/extensions/sandbox",
            "Sandbox extension code may have backend-specific tests.",
        )
        plan.note("Some sandbox extension tests may require optional services such as Docker or hosted providers.")

    if has_prefix(path, "src/agents/extensions/memory"):
        plan.add(
            "uv run pytest -s tests/memory tests/extensions/memory",
            "Memory/session extension code changed; run memory backend tests.",
        )

    if has_suffix(path, "run_config.py", "model_settings.py", "tool.py", "run_context.py", "result.py"):
        plan.add(
            "uv run pytest -s tests/test_source_compat_constructors.py",
            "Public constructor/dataclass surface changed; verify positional compatibility.",
        )
        plan.note("Append optional public fields where possible; preserve released positional meanings.")

    if has_prefix(path, "tests"):
        plan.full_verification_recommended = True
        plan.pr_summary_recommended = True
        if path.endswith(".py"):
            plan.add(f"uv run pytest -s {path}", "A test file changed; run the edited test file first.")
        if "snapshot" in path or path.endswith(".snap"):
            plan.snapshot_review_recommended = True
            plan.note("Snapshot updates should be reviewed and followed by make tests.")

    if has_prefix(path, "examples"):
        plan.full_verification_recommended = True
        plan.pr_summary_recommended = True
        plan.add("make tests", "Examples changed; full tests are required by repo policy.", "final")

    if has_prefix(path, "docs") or path == "mkdocs.yml":
        plan.docs_build_recommended = True
        if has_prefix(path, "docs/ja", "docs/ko", "docs/zh"):
            plan.note("Translated docs are generated; edit them only for explicit translation maintenance tasks.")
        plan.add("make build-docs", "Docs or MkDocs config changed; build docs before handoff.")
        if has_prefix(path, "docs/scripts") or path == "mkdocs.yml":
            plan.full_verification_recommended = True
            plan.pr_summary_recommended = True
            plan.add("make lint", "Docs scripts or build config changed; lint is required by repo policy.", "final")
            plan.add("make typecheck", "Docs scripts or build config changed; typecheck is required by repo policy.", "final")
            plan.add("make tests", "Docs scripts or build config changed; tests are required by repo policy.", "final")

    if path in {"Makefile", "pyproject.toml", "uv.lock"} or has_prefix(path, ".github/workflows"):
        plan.full_verification_recommended = True
        plan.pr_summary_recommended = True
        plan.add("make format", "Build/test configuration changed; run formatter in the final stack.", "final")
        plan.add("make lint", "Build/test configuration changed; run lint in the final stack.", "final")
        plan.add("make typecheck", "Build/test configuration changed; run typecheck in the final stack.", "final")
        plan.add("make tests", "Build/test configuration changed; run tests in the final stack.", "final")

    if path == "pyproject.toml":
        plan.add("make sync", "Project dependencies or tool config changed; refresh the uv environment when needed.")
        plan.add("make format-check", "Ruff configuration may affect formatting behavior.")

    if path == "Makefile":
        plan.add("make check", "Make targets changed; run the aggregate check when appropriate.")

    if has_prefix(path, ".github/scripts"):
        plan.full_verification_recommended = True
        plan.pr_summary_recommended = True
        plan.note("CI scripts are maintainer automation; inspect for service assumptions before running directly.")


def build_plan(paths: Iterable[str]) -> Plan:
    normalized_paths = [normalize_path(path) for path in paths]
    plan = Plan(changed_paths=normalized_paths)

    for path in normalized_paths:
        suggest_for_path(plan, path)

    if plan.full_verification_recommended:
        plan.note("Repository policy requires final code-change verification for these paths.")
    if plan.pr_summary_recommended:
        plan.note("Repository policy requires a PR draft summary before final handoff for eligible changes.")
    if plan.docs_build_recommended:
        plan.note("Treat runnable docs snippets as API compatibility checks.")
    if not plan.suggestions:
        plan.note("No focused commands matched; inspect the changed area and run the nearest relevant tests.")

    return plan


def plan_to_json(plan: Plan) -> dict[str, object]:
    return {
        "changed_paths": plan.changed_paths,
        "full_verification_recommended": plan.full_verification_recommended,
        "docs_build_recommended": plan.docs_build_recommended,
        "snapshot_review_recommended": plan.snapshot_review_recommended,
        "pr_summary_recommended": plan.pr_summary_recommended,
        "suggestions": [suggestion.__dict__ for suggestion in plan.suggestions],
        "notes": plan.notes,
    }


def print_text(plan: Plan) -> None:
    print("Changed paths:")
    for path in plan.changed_paths:
        print(f"- {path}")

    print("\nSuggested commands:")
    if plan.suggestions:
        for suggestion in plan.suggestions:
            print(f"- [{suggestion.when}] {suggestion.command}")
            print(f"  Reason: {suggestion.reason}")
    else:
        print("- No focused command matched.")

    if plan.notes:
        print("\nNotes:")
        for note in plan.notes:
            print(f"- {note}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Suggest focused validation commands for changed openai-agents-python files."
    )
    parser.add_argument("paths", nargs="*", help="Changed file paths relative to the repository root.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of human-readable text.",
    )
    parser.add_argument(
        "--from-stdin",
        action="store_true",
        help="Read additional newline-delimited paths from standard input.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = list(args.paths)

    if args.from_stdin:
        try:
            while True:
                paths.append(input())
        except EOFError:
            pass

    if not paths:
        raise SystemExit("Provide at least one changed path, or use --from-stdin.")

    plan = build_plan(paths)
    if args.json:
        print(json.dumps(plan_to_json(plan), indent=2, sort_keys=True))
    else:
        print_text(plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
