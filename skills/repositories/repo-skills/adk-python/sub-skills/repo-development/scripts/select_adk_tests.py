#!/usr/bin/env python3
"""Suggest focused ADK Python repo validation checks without running them.

The script accepts changed file paths or capability names and prints likely
pytest targets plus related docs, sample, schema, and credential notes. It is
safe to run from any current working directory because it only inspects the
provided strings and emits suggestions.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import PurePosixPath
import sys
from typing import Iterable


@dataclass(frozen=True)
class Suggestion:
  command: str
  reason: str


@dataclass(frozen=True)
class Rule:
  labels: tuple[str, ...]
  prefixes: tuple[str, ...]
  keywords: tuple[str, ...]
  suggestions: tuple[Suggestion, ...]
  notes: tuple[str, ...] = ()


RULES: tuple[Rule, ...] = (
    Rule(
        labels=("agents", "llm-agent"),
        prefixes=("src/google/adk/agents/",),
        keywords=("agent", "llmagent", "sub_agent", "callback"),
        suggestions=(
            Suggestion(
                "pytest tests/unittests/agents -q",
                "Agent and LlmAgent unit behavior.",
            ),
            Suggestion(
                "pytest tests/unittests/flows/llm_flows -q",
                "LLM flow behavior affected by agent execution changes.",
            ),
            Suggestion(
                "pytest tests/integration/test_single_agent.py -q",
                "Focused end-to-end single-agent smoke coverage.",
            ),
            Suggestion(
                "pytest tests/integration/test_multi_agent.py -q",
                "Sub-agent and delegation integration coverage.",
            ),
        ),
    ),
    Rule(
        labels=("workflow", "hitl", "resume"),
        prefixes=("src/google/adk/workflow/",),
        keywords=(
            "workflow",
            "node",
            "join",
            "parallel",
            "dynamic",
            "hitl",
            "resume",
            "checkpoint",
            "rerun_on_resume",
        ),
        suggestions=(
            Suggestion(
                "pytest tests/unittests/workflow -q",
                "Workflow graph, node, join, dynamic, and retry behavior.",
            ),
            Suggestion(
                "pytest tests/unittests/events -q",
                "Event output and state-delta behavior used by workflows.",
            ),
            Suggestion(
                "pytest tests/unittests/runners/test_pause_invocation.py -q",
                "Pause/HITL runner behavior when interruption semantics change.",
            ),
            Suggestion(
                "pytest tests/unittests/runners/test_resume_invocation.py -q",
                "Resume behavior and duplicate-event regression coverage.",
            ),
        ),
    ),
    Rule(
        labels=("runners",),
        prefixes=("src/google/adk/runners.py", "src/google/adk/runners/"),
        keywords=("runner", "run_config", "invocation"),
        suggestions=(
            Suggestion(
                "pytest tests/unittests/runners -q",
                "Runner unit behavior and invocation lifecycle.",
            ),
            Suggestion(
                "pytest tests/integration/test_multi_turn.py -q",
                "Multi-turn runner behavior across sessions.",
            ),
        ),
    ),
    Rule(
        labels=("events",),
        prefixes=("src/google/adk/events/",),
        keywords=("event", "state_delta", "actions"),
        suggestions=(
            Suggestion("pytest tests/unittests/events -q", "Event models."),
            Suggestion(
                "pytest tests/unittests/runners -q",
                "Runner/event integration behavior.",
            ),
        ),
    ),
    Rule(
        labels=("sessions",),
        prefixes=("src/google/adk/sessions/",),
        keywords=("session", "sessions", "database_session"),
        suggestions=(
            Suggestion("pytest tests/unittests/sessions -q", "Session services."),
            Suggestion(
                "pytest tests/unittests/sessions/migration -q",
                "Persistence migration behavior when storage schemas change.",
            ),
        ),
        notes=("Database-backed tests may require the db extra.",),
    ),
    Rule(
        labels=("memory",),
        prefixes=("src/google/adk/memory/",),
        keywords=("memory",),
        suggestions=(
            Suggestion("pytest tests/unittests/memory -q", "Memory services."),
        ),
    ),
    Rule(
        labels=("artifacts",),
        prefixes=("src/google/adk/artifacts/",),
        keywords=("artifact", "artifacts"),
        suggestions=(
            Suggestion(
                "pytest tests/unittests/artifacts -q",
                "Artifact services and persistence behavior.",
            ),
        ),
    ),
    Rule(
        labels=("plugins",),
        prefixes=("src/google/adk/plugins/",),
        keywords=("plugin", "plugins"),
        suggestions=(
            Suggestion("pytest tests/unittests/plugins -q", "Plugin hooks."),
            Suggestion(
                "pytest tests/unittests/runners -q",
                "Runner ownership of plugin lifecycle.",
            ),
        ),
    ),
    Rule(
        labels=("telemetry",),
        prefixes=("src/google/adk/telemetry/",),
        keywords=("telemetry", "tracing", "metrics", "opentelemetry"),
        suggestions=(
            Suggestion(
                "pytest tests/unittests/telemetry -q",
                "Telemetry and tracing unit behavior.",
            ),
        ),
        notes=("GCP telemetry exporters require optional extras and credentials.",),
    ),
    Rule(
        labels=("code-executors",),
        prefixes=("src/google/adk/code_executors/",),
        keywords=("code_executor", "code executors", "sandbox", "execution"),
        suggestions=(
            Suggestion(
                "pytest tests/unittests/code_executors -q",
                "Code executor safety and behavior.",
            ),
        ),
        notes=("Container or remote executor checks can require optional extras.",),
    ),
    Rule(
        labels=("tools",),
        prefixes=("src/google/adk/tools/",),
        keywords=(
            "tool",
            "tools",
            "functiontool",
            "toolcontext",
            "toolset",
            "mcp",
            "openapi",
        ),
        suggestions=(
            Suggestion("pytest tests/unittests/tools -q", "Tool behavior."),
            Suggestion(
                "pytest tests/integration/test_tools.py -q",
                "Focused tool integration coverage.",
            ),
        ),
        notes=("MCP, OpenAPI, cloud, and extension toolsets may need extras.",),
    ),
    Rule(
        labels=("auth",),
        prefixes=("src/google/adk/auth/",),
        keywords=("auth", "credential", "oauth"),
        suggestions=(
            Suggestion("pytest tests/unittests/auth -q", "Auth services."),
        ),
        notes=("Live auth flows can require credentials; prefer mocked tests.",),
    ),
    Rule(
        labels=("integrations",),
        prefixes=("src/google/adk/integrations/",),
        keywords=(
            "integration",
            "bigquery",
            "bigtable",
            "firestore",
            "gcs",
            "spanner",
            "slack",
            "langgraph",
            "crewai",
        ),
        suggestions=(
            Suggestion(
                "pytest tests/unittests/integrations -q",
                "Integration unit tests; narrow to provider subdirectory when known.",
            ),
        ),
        notes=(
            "Provider tests often require optional extras, credentials, or network.",
        ),
    ),
    Rule(
        labels=("a2a",),
        prefixes=("src/google/adk/a2a/",),
        keywords=("a2a", "agent-to-agent"),
        suggestions=(
            Suggestion("pytest tests/unittests/a2a -q", "A2A unit coverage."),
        ),
        notes=("A2A tests may require the a2a extra.",),
    ),
    Rule(
        labels=("cli", "config", "schema"),
        prefixes=(
            "src/google/adk/cli/",
            "src/google/adk/agents/config_schemas/",
            "src/google/adk/apps/",
        ),
        keywords=("cli", "adk run", "adk web", "api_server", "config", "yaml", "schema"),
        suggestions=(
            Suggestion("pytest tests/unittests/cli -q", "CLI unit coverage."),
            Suggestion(
                "pytest tests/integration/test_cli_run.py -q",
                "CLI run integration behavior.",
            ),
            Suggestion(
                "python scripts/generate_agent_config_schema.py",
                "Regenerate AgentConfig.json if config models or descriptions changed.",
            ),
            Suggestion(
                "git diff -- src/google/adk/agents/config_schemas/AgentConfig.json",
                "Review generated schema changes before accepting them.",
            ),
        ),
    ),
    Rule(
        labels=("evaluation", "eval"),
        prefixes=("src/google/adk/evaluation/",),
        keywords=("evaluation", "eval", "eval_set", "adk test"),
        suggestions=(
            Suggestion(
                "pytest tests/unittests/evaluation -q",
                "Evaluation framework unit coverage.",
            ),
            Suggestion(
                "pytest tests/integration/test_evaluate_agent_in_fixture.py -q",
                "Fixture-based eval integration behavior.",
            ),
            Suggestion(
                "pytest tests/integration/test_with_test_file.py -q",
                "JSON test-file execution behavior.",
            ),
        ),
        notes=("Live model evaluation can be flaky or credential-dependent.",),
    ),
    Rule(
        labels=("models",),
        prefixes=("src/google/adk/models/",),
        keywords=("model", "llm", "gemini", "litellm"),
        suggestions=(
            Suggestion("pytest tests/unittests/models -q", "Model adapter units."),
            Suggestion(
                "pytest tests/integration/models -q",
                "Model integration tests; check credentials and provider setup first.",
            ),
        ),
        notes=("Provider integration tests can need API keys and network.",),
    ),
    Rule(
        labels=("planners",),
        prefixes=("src/google/adk/planners/",),
        keywords=("planner", "planning"),
        suggestions=(
            Suggestion("pytest tests/unittests/planners -q", "Planner units."),
        ),
    ),
    Rule(
        labels=("flows",),
        prefixes=("src/google/adk/flows/",),
        keywords=("flow", "llm_flow", "llm flows"),
        suggestions=(
            Suggestion("pytest tests/unittests/flows -q", "Flow units."),
            Suggestion(
                "pytest tests/integration/test_single_agent.py -q",
                "Agent flow smoke behavior.",
            ),
        ),
    ),
    Rule(
        labels=("docs",),
        prefixes=("docs/",),
        keywords=("docs", "guide", "guides", "documentation"),
        suggestions=(
            Suggestion(
                "pre-commit run mdformat --files <changed-docs>",
                "Markdown formatting for changed docs when pre-commit is available.",
            ),
            Suggestion(
                "python -m pytest <tests-for-documented-api> -q",
                "Run code tests for APIs demonstrated in changed guides.",
            ),
        ),
        notes=("New or retitled guides may need the guides index updated.",)
    ),
    Rule(
        labels=("samples",),
        prefixes=("contributing/samples/",),
        keywords=("sample", "samples", "example"),
        suggestions=(
            Suggestion(
                "python -m py_compile <changed-sample-python-files>",
                "Syntax-check sample files when no dedicated test exists.",
            ),
            Suggestion(
                "adk run --help && adk web --help",
                "Safe CLI availability checks without launching a server.",
            ),
        ),
        notes=(
            "Sample agents should not hardcode model= unless explicitly required.",
        ),
    ),
    Rule(
        labels=("packaging", "dependencies"),
        prefixes=("pyproject.toml", "uv.lock"),
        keywords=("dependency", "dependencies", "extra", "pyproject", "packaging"),
        suggestions=(
            Suggestion("uv sync --all-extras", "Dependency resolution check."),
            Suggestion("uv build", "Build metadata and package artifact check."),
            Suggestion("pytest tests/unittests -q", "Broad unit safety net for dependency changes."),
        ),
    ),
)

BASELINE_SUGGESTIONS: tuple[Suggestion, ...] = (
    Suggestion(
        "pre-commit run --files <changed-files>",
        "Run configured formatting, import, lint, license, and markdown checks on touched files.",
    ),
)

REMOTE_WARNING = (
    "Remote/cloud/model tests may require credentials, network, deployed resources, "
    "or optional extras; skip them unless explicitly authorized."
)


def normalize_token(token: str) -> str:
  return token.strip().replace("\\", "/").lstrip("./").lower()


def matches_rule(token: str, rule: Rule) -> bool:
  normalized = normalize_token(token)
  if not normalized:
    return False

  path = PurePosixPath(normalized)
  path_text = path.as_posix()
  if any(
      path_text == prefix.rstrip("/") or path_text.startswith(prefix)
      for prefix in rule.prefixes
  ):
    return True

  compact = path_text.replace("-", "_").replace(" ", "_")
  parts = set(compact.replace("/", "_").split("_"))
  keyword_forms = {keyword.replace("-", "_").replace(" ", "_") for keyword in rule.keywords}
  return compact in keyword_forms or any(keyword in parts for keyword in keyword_forms)


def collect(tokens: Iterable[str]) -> tuple[list[Suggestion], list[str], list[str]]:
  suggestions: list[Suggestion] = list(BASELINE_SUGGESTIONS)
  notes: list[str] = []
  matched_labels: list[str] = []
  seen_commands = {suggestion.command for suggestion in suggestions}
  seen_notes: set[str] = set()

  for token in tokens:
    for rule in RULES:
      if not matches_rule(token, rule):
        continue
      for label in rule.labels:
        if label not in matched_labels:
          matched_labels.append(label)
      for suggestion in rule.suggestions:
        if suggestion.command not in seen_commands:
          suggestions.append(suggestion)
          seen_commands.add(suggestion.command)
      for note in rule.notes:
        if note not in seen_notes:
          notes.append(note)
          seen_notes.add(note)

  if not matched_labels:
    suggestions.append(
        Suggestion(
            "pytest tests/unittests -q",
            "Fallback unit suite when the changed area is unknown.",
        )
    )
    notes.append(
        "No specific ADK area matched; inspect the diff and narrow manually."
    )

  if REMOTE_WARNING not in seen_notes:
    notes.append(REMOTE_WARNING)

  return suggestions, notes, matched_labels


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
      description=(
          "Suggest focused validation commands for ADK Python repo changes. "
          "Inputs may be file paths or capability names. The script never runs tests."
      )
  )
  parser.add_argument(
      "items",
      nargs="*",
      help="Changed file paths or capability names such as workflow, tools, cli, docs.",
  )
  parser.add_argument(
      "--from-file",
      metavar="PATH",
      help="Read newline-separated changed paths or capability names from a file; use '-' for stdin.",
  )
  return parser


def read_items(args: argparse.Namespace) -> list[str]:
  items = list(args.items)
  if args.from_file:
    if args.from_file == "-":
      items.extend(line.strip() for line in sys.stdin if line.strip())
    else:
      with open(args.from_file, encoding="utf-8") as handle:
        items.extend(line.strip() for line in handle if line.strip())
  return items


def main(argv: list[str] | None = None) -> int:
  parser = build_parser()
  args = parser.parse_args(argv)
  items = read_items(args)

  if not items:
    parser.print_help()
    return 0

  suggestions, notes, matched_labels = collect(items)

  print("Matched areas:")
  if matched_labels:
    for label in matched_labels:
      print(f"- {label}")
  else:
    print("- unknown")

  print("\nSuggested checks (not run):")
  for suggestion in suggestions:
    print(f"- {suggestion.command}")
    print(f"  reason: {suggestion.reason}")

  print("\nNotes:")
  for note in notes:
    print(f"- {note}")

  return 0


if __name__ == "__main__":
  raise SystemExit(main())
