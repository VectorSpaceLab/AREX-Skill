#!/usr/bin/env python3
"""Validate a CrewAI JSONC crew definition without executing project code.

The checker parses crew.jsonc/crew.json and agent JSONC/JSON files, validates
common runtime shape errors, and reports trust-boundary warnings for Python
callback references and custom tools. It does not import CrewAI, import project
modules, call LLMs, access the network, or execute callbacks/tools.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

LINE_COMMENT_RE = re.compile(r"//.*?(?=\n|$)")
BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
TRAILING_COMMA_RE = re.compile(r",\s*([}\]])")
PLACEHOLDER_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_\-]*)\}")
PYTHON_REF_KEYS = {
    "callback",
    "step_callback",
    "task_callback",
    "guardrail",
    "condition",
    "converter_cls",
}
CALLBACK_LIST_KEYS = {
    "callbacks",
    "before_kickoff_callbacks",
    "after_kickoff_callbacks",
}


@dataclass
class Finding:
    severity: str
    location: str
    message: str


@dataclass
class ValidationReport:
    errors: list[Finding] = field(default_factory=list)
    warnings: list[Finding] = field(default_factory=list)

    def error(self, location: str, message: str) -> None:
        self.errors.append(Finding("error", location, message))

    def warning(self, location: str, message: str) -> None:
        self.warnings.append(Finding("warning", location, message))

    def extend(self, other: "ValidationReport") -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


def strip_jsonc(source: str) -> str:
    """Remove JSONC comments and trailing commas while preserving strings."""

    result: list[str] = []
    index = 0
    in_string = False
    escape = False
    while index < len(source):
        char = source[index]
        next_char = source[index + 1] if index + 1 < len(source) else ""

        if in_string:
            result.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            index += 1
            continue

        if char == '"':
            in_string = True
            result.append(char)
            index += 1
            continue

        if char == "/" and next_char == "/":
            index += 2
            while index < len(source) and source[index] not in "\r\n":
                index += 1
            continue

        if char == "/" and next_char == "*":
            index += 2
            while index + 1 < len(source) and not (
                source[index] == "*" and source[index + 1] == "/"
            ):
                index += 1
            index += 2
            continue

        result.append(char)
        index += 1

    stripped = "".join(result)
    previous = None
    while previous != stripped:
        previous = stripped
        stripped = TRAILING_COMMA_RE.sub(r"\1", stripped)
    return stripped


def load_jsonc(path: Path, report: ValidationReport) -> Any | None:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        report.error(str(path), f"Cannot read file: {exc}")
        return None

    try:
        return json.loads(strip_jsonc(source))
    except json.JSONDecodeError as exc:
        report.error(str(path), f"Invalid JSON/JSONC: {exc.msg} at line {exc.lineno}, column {exc.colno}")
        return None


def find_project_file(project_dir: Path, stem: str) -> Path | None:
    jsonc_path = project_dir / f"{stem}.jsonc"
    json_path = project_dir / f"{stem}.json"
    if jsonc_path.exists():
        return jsonc_path
    if json_path.exists():
        return json_path
    return None


def find_agent_file(project_dir: Path, agent_name: str) -> Path | None:
    agent_dir = project_dir / "agents"
    jsonc_path = agent_dir / f"{agent_name}.jsonc"
    json_path = agent_dir / f"{agent_name}.json"
    if jsonc_path.exists():
        return jsonc_path
    if json_path.exists():
        return json_path
    return None


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def merge_settings(document: dict[str, Any]) -> dict[str, Any]:
    merged = dict(document)
    settings = merged.get("settings")
    if isinstance(settings, dict):
        merged.update(settings)
    return merged


def iter_nested(value: Any, path: str = ""):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            yield from iter_nested(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]" if path else f"[{index}]"
            yield from iter_nested(child, child_path)


def warn_python_refs(value: Any, report: ValidationReport, location: str) -> None:
    for nested_path, nested_value in iter_nested(value):
        if isinstance(nested_value, dict) and "python" in nested_value:
            python_ref = nested_value.get("python")
            if is_non_empty_string(python_ref):
                report.warning(
                    f"{location}:{nested_path}",
                    f"Python reference {python_ref!r} executes local code when CrewAI loads the project; review before running.",
                )
            else:
                report.error(
                    f"{location}:{nested_path}",
                    "Python reference must be a non-empty string.",
                )
        if isinstance(nested_value, str) and nested_value.startswith("custom:"):
            report.warning(
                f"{location}:{nested_path}",
                f"Custom tool {nested_value!r} loads project Python code; review tools before running.",
            )


def collect_placeholders(value: Any) -> set[str]:
    placeholders: set[str] = set()
    for _, nested_value in iter_nested(value):
        if isinstance(nested_value, str):
            placeholders.update(PLACEHOLDER_RE.findall(nested_value))
    return placeholders


def validate_agent(project_dir: Path, agent_name: str, report: ValidationReport) -> dict[str, Any] | None:
    agent_path = find_agent_file(project_dir, agent_name)
    if agent_path is None:
        report.error(
            f"agents/{agent_name}",
            f"Missing agent file; expected agents/{agent_name}.jsonc or agents/{agent_name}.json.",
        )
        return None

    document = load_jsonc(agent_path, report)
    if document is None:
        return None
    if not isinstance(document, dict):
        report.error(str(agent_path), "Agent file must contain a JSON object.")
        return None

    merged = merge_settings(document)
    for required in ("role", "goal", "backstory"):
        if not is_non_empty_string(merged.get(required)):
            report.error(str(agent_path), f"Agent {agent_name!r} missing non-empty {required!r}.")

    warn_python_refs(document, report, str(agent_path))
    return document


def validate_tasks(crew: dict[str, Any], declared_agents: set[str], report: ValidationReport) -> None:
    tasks = crew.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        report.error("crew.tasks", "Crew must define a non-empty tasks list.")
        return

    seen_task_names: set[str] = set()
    generated_names: set[str] = set()
    process = crew.get("process", "sequential")
    is_hierarchical = process == "hierarchical"

    for index, task in enumerate(tasks):
        location = f"crew.tasks[{index}]"
        if not isinstance(task, dict):
            report.error(location, "Task entry must be an object.")
            continue

        task_name = task.get("name")
        if is_non_empty_string(task_name):
            normalized_name = str(task_name)
        else:
            normalized_name = f"__task_{index}"
            generated_names.add(normalized_name)
            report.warning(location, "Task has no name; add one for stable JSONC context references.")

        if normalized_name in seen_task_names:
            report.error(location, f"Duplicate task name {normalized_name!r}.")
        seen_task_names.add(normalized_name)

        for required in ("description", "expected_output"):
            if not is_non_empty_string(task.get(required)):
                report.error(location, f"Task {normalized_name!r} missing non-empty {required!r}.")

        agent_ref = task.get("agent")
        if agent_ref is not None:
            if not is_non_empty_string(agent_ref):
                report.error(location, "Task agent must be a non-empty string when provided.")
            elif agent_ref not in declared_agents:
                report.error(location, f"Task agent {agent_ref!r} is not listed in crew.agents.")
        elif not is_hierarchical:
            report.warning(location, "Sequential task has no agent; assign an agent or switch to hierarchical process.")

        context = task.get("context")
        if context is not None:
            if not isinstance(context, list):
                report.error(location, "Task context must be a list of prior task names.")
            else:
                for ref in context:
                    if not is_non_empty_string(ref):
                        report.error(location, "Task context entries must be non-empty strings.")
                    elif ref not in seen_task_names or ref == normalized_name:
                        report.error(
                            location,
                            f"Task context {ref!r} must reference a previously listed task; forward references are invalid.",
                        )
                    elif ref in generated_names:
                        report.warning(location, f"Context {ref!r} points to an unnamed generated task; use explicit task names.")

        if task.get("output_json") and task.get("output_pydantic"):
            report.error(location, "Set only one of output_json or output_pydantic.")

        if "max_retries" in task:
            report.warning(location, "max_retries is deprecated for guardrails; use guardrail_max_retries.")

        retry_value = task.get("guardrail_max_retries")
        if retry_value is not None:
            if not isinstance(retry_value, int) or retry_value < 0:
                report.error(location, "guardrail_max_retries must be a non-negative integer.")
            elif retry_value > 5:
                report.warning(location, "guardrail_max_retries above 5 can create expensive retry loops.")

        if task.get("guardrail") and task.get("guardrails"):
            report.warning(location, "guardrails takes precedence over guardrail; single guardrail will be ignored.")

        warn_python_refs(task, report, location)


def validate_crew(project_dir: Path, strict_warnings: bool = False) -> tuple[ValidationReport, dict[str, Any] | None]:
    report = ValidationReport()
    crew_path = find_project_file(project_dir, "crew")
    if crew_path is None:
        report.error(str(project_dir), "Missing crew.jsonc or crew.json.")
        return report, None

    crew = load_jsonc(crew_path, report)
    if crew is None:
        return report, None
    if not isinstance(crew, dict):
        report.error(str(crew_path), "Crew file must contain a JSON object.")
        return report, None

    process = crew.get("process", "sequential")
    if process not in {"sequential", "hierarchical"}:
        report.error("crew.process", "Process must be 'sequential' or 'hierarchical'.")

    agent_names = crew.get("agents")
    declared_agents: set[str] = set()
    if not isinstance(agent_names, list) or not agent_names:
        report.error("crew.agents", "Crew must define a non-empty agents list.")
    else:
        for index, name in enumerate(agent_names):
            if not is_non_empty_string(name):
                report.error(f"crew.agents[{index}]", "Agent names must be non-empty strings.")
                continue
            if name in declared_agents:
                report.error(f"crew.agents[{index}]", f"Duplicate agent name {name!r}.")
                continue
            declared_agents.add(name)
            validate_agent(project_dir, name, report)

    if process == "hierarchical":
        manager_llm = crew.get("manager_llm")
        manager_agent = crew.get("manager_agent")
        if not manager_llm and not manager_agent:
            report.error("crew", "Hierarchical process requires manager_llm or manager_agent.")
        if is_non_empty_string(manager_agent) and manager_agent in declared_agents:
            report.error("crew.manager_agent", "Custom manager_agent must not also appear in crew.agents.")
        if is_non_empty_string(manager_agent):
            validate_agent(project_dir, manager_agent, report)

    validate_tasks(crew, declared_agents, report)
    warn_python_refs(crew, report, str(crew_path))

    inputs = crew.get("inputs", {})
    if inputs is not None and not isinstance(inputs, dict):
        report.error("crew.inputs", "inputs must be an object when provided.")
        input_keys: set[str] = set()
    else:
        input_keys = set(inputs.keys()) if isinstance(inputs, dict) else set()

    placeholders = collect_placeholders(crew)
    missing_inputs = sorted(placeholders - input_keys)
    for placeholder in missing_inputs:
        report.warning(
            "crew.inputs",
            f"Placeholder {{{placeholder}}} has no default input; CLI may prompt at runtime.",
        )

    if strict_warnings and report.warnings:
        for warning in report.warnings:
            report.errors.append(
                Finding("error", warning.location, f"Strict warning: {warning.message}")
            )

    return report, crew


def print_report(report: ValidationReport) -> None:
    if not report.errors and not report.warnings:
        print("OK: Crew definition passed static shape checks.")
        return

    for finding in report.errors + report.warnings:
        print(f"{finding.severity.upper()}: {finding.location}: {finding.message}")

    print(
        f"Summary: {len(report.errors)} error(s), {len(report.warnings)} warning(s)."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a CrewAI JSONC crew project without importing project code, "
            "running tools, calling LLMs, or accessing the network."
        )
    )
    parser.add_argument(
        "project_dir",
        type=Path,
        help="Directory containing crew.jsonc/crew.json and agents/.",
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Treat trust and quality warnings as failures.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    project_dir = args.project_dir.resolve()

    if not project_dir.exists() or not project_dir.is_dir():
        print(f"ERROR: {project_dir}: project_dir must be an existing directory.", file=sys.stderr)
        return 2

    report, _ = validate_crew(project_dir, strict_warnings=args.strict_warnings)
    print_report(report)
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
