#!/usr/bin/env python3
"""Inspect OpenAI Agents Python core runtime surfaces without network calls."""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from importlib import metadata
from typing import Any


REQUIRED_SURFACES = {
    "agents": ["Agent", "Runner", "RunConfig"],
    "agents.run_state": ["RunState"],
}

SIGNATURE_TARGETS = [
    ("agents", "Agent"),
    ("agents", "RunConfig"),
    ("agents", "Runner.run"),
    ("agents", "Runner.run_sync"),
    ("agents", "Runner.run_streamed"),
    ("agents.run_state", "RunState"),
]

EXPECTED_PARAMETERS = {
    "agents.Agent": [
        "name",
        "instructions",
        "prompt",
        "handoffs",
        "model",
        "model_settings",
        "input_guardrails",
        "output_guardrails",
        "output_type",
        "tool_use_behavior",
        "reset_tool_choice",
    ],
    "agents.RunConfig": [
        "model",
        "model_provider",
        "model_settings",
        "handoff_input_filter",
        "input_guardrails",
        "output_guardrails",
        "tracing_disabled",
        "session_input_callback",
        "call_model_input_filter",
        "tool_error_formatter",
        "session_settings",
        "reasoning_item_id_policy",
        "sandbox",
        "tool_execution",
        "tool_not_found_behavior",
    ],
    "agents.Runner.run": [
        "starting_agent",
        "input",
        "context",
        "max_turns",
        "hooks",
        "run_config",
        "error_handlers",
        "previous_response_id",
        "auto_previous_response_id",
        "conversation_id",
        "session",
    ],
    "agents.Runner.run_sync": [
        "starting_agent",
        "input",
        "context",
        "max_turns",
        "hooks",
        "run_config",
        "error_handlers",
        "previous_response_id",
        "auto_previous_response_id",
        "conversation_id",
        "session",
    ],
    "agents.Runner.run_streamed": [
        "starting_agent",
        "input",
        "context",
        "max_turns",
        "hooks",
        "run_config",
        "error_handlers",
        "previous_response_id",
        "auto_previous_response_id",
        "conversation_id",
        "session",
    ],
    "agents.run_state.RunState": [
        "context",
        "original_input",
        "starting_agent",
        "max_turns",
        "conversation_id",
        "previous_response_id",
        "auto_previous_response_id",
    ],
}


def resolve_attr(module: Any, dotted_name: str) -> Any:
    target = module
    for part in dotted_name.split("."):
        target = getattr(target, part)
    return target


def signature_text(target: Any) -> str:
    return str(inspect.signature(target))


def parameter_names(target: Any) -> list[str]:
    return list(inspect.signature(target).parameters)


def inspect_runtime() -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    report: dict[str, Any] = {
        "distribution": "openai-agents",
        "version": None,
        "modules": {},
        "signatures": {},
        "errors": [],
    }

    try:
        report["version"] = metadata.version("openai-agents")
    except metadata.PackageNotFoundError:
        errors.append("Distribution 'openai-agents' is not installed or not visible.")

    imported_modules: dict[str, Any] = {}
    for module_name, names in REQUIRED_SURFACES.items():
        module_report = {"imported": False, "missing": []}
        try:
            module = importlib.import_module(module_name)
            imported_modules[module_name] = module
            module_report["imported"] = True
        except Exception as exc:
            errors.append(f"Failed to import {module_name}: {exc}")
            report["modules"][module_name] = module_report
            continue

        for name in names:
            if not hasattr(module, name):
                module_report["missing"].append(name)
                errors.append(f"Missing {module_name}.{name}")
        report["modules"][module_name] = module_report

    for module_name, dotted_name in SIGNATURE_TARGETS:
        key = f"{module_name}.{dotted_name}"
        module = imported_modules.get(module_name)
        if module is None:
            continue
        try:
            target = resolve_attr(module, dotted_name)
            params = parameter_names(target)
            report["signatures"][key] = {
                "signature": signature_text(target),
                "parameters": params,
            }
        except Exception as exc:
            errors.append(f"Could not inspect signature for {key}: {exc}")
            continue

        missing_params = [param for param in EXPECTED_PARAMETERS[key] if param not in params]
        if missing_params:
            errors.append(f"{key} missing expected parameters: {', '.join(missing_params)}")
            report["signatures"][key]["missing_expected_parameters"] = missing_params

    report["ok"] = not errors
    report["errors"] = errors
    return report, errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import agents core runtime surfaces and validate expected signatures. "
            "This helper performs no network or model calls."
        )
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report, errors = inspect_runtime()

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Distribution: {report['distribution']}")
        print(f"Version: {report.get('version') or 'not found'}")
        for module_name, module_report in report["modules"].items():
            status = "ok" if module_report["imported"] and not module_report["missing"] else "problem"
            print(f"Module {module_name}: {status}")
            if module_report["missing"]:
                print(f"  missing: {', '.join(module_report['missing'])}")
        for key, signature_report in report["signatures"].items():
            print(f"{key}{signature_report['signature']}")
            missing = signature_report.get("missing_expected_parameters")
            if missing:
                print(f"  missing expected parameters: {', '.join(missing)}")
        if errors:
            print("Errors:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
