#!/usr/bin/env python3
"""Validate Prefect automation JSON/YAML without contacting a Prefect API."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - depends on runtime install
    yaml = None


DEPLOYMENT_EVENT_EXAMPLE: dict[str, Any] = {
    "name": "run-downstream-on-upstream-completed",
    "description": "Runs a downstream deployment when a selected upstream deployment completes.",
    "enabled": True,
    "tags": ["event-driven", "deployment"],
    "trigger": {
        "type": "event",
        "posture": "Reactive",
        "expect": ["prefect.flow-run.Completed"],
        "match": {"prefect.resource.id": "prefect.flow-run.*"},
        "match_related": {
            "prefect.resource.id": "prefect.deployment.00000000-0000-0000-0000-000000000000",
            "prefect.resource.role": "deployment",
        },
        "for_each": ["prefect.resource.id"],
        "threshold": 1,
        "within": 0,
    },
    "actions": [
        {
            "type": "run-deployment",
            "source": "selected",
            "deployment_id": "11111111-1111-1111-1111-111111111111",
            "parameters": {
                "upstream_flow_run_id": "{{ event.resource.id }}",
                "event_payload": {"template": "{{ event.payload | tojson }}"},
            },
        }
    ],
    "actions_on_trigger": [],
    "actions_on_resolve": [],
}

NOTIFICATION_EXAMPLE: dict[str, Any] = {
    "name": "notify-on-flow-failure",
    "description": "Sends a saved notification block when any flow run fails.",
    "enabled": True,
    "trigger": {
        "type": "event",
        "posture": "Reactive",
        "expect": ["prefect.flow-run.Failed", "prefect.flow-run.Crashed"],
        "match": {"prefect.resource.id": "prefect.flow-run.*"},
        "for_each": ["prefect.resource.id"],
        "threshold": 1,
        "within": 0,
    },
    "actions": [
        {
            "type": "send-notification",
            "block_document_id": "22222222-2222-2222-2222-222222222222",
            "subject": "Prefect flow run failed",
            "body": "Flow run {{ event.resource.id }} emitted {{ event.event }}.",
        }
    ],
}

PROACTIVE_EXAMPLE: dict[str, Any] = {
    "name": "alert-when-heartbeat-missing",
    "description": "Fires when an expected heartbeat-like custom event is absent.",
    "enabled": True,
    "trigger": {
        "type": "event",
        "posture": "Proactive",
        "expect": ["external.extract.heartbeat"],
        "match": {"prefect.resource.id": "extractor.prod"},
        "for_each": ["prefect.resource.id"],
        "threshold": 1,
        "within": 60,
    },
    "actions": [{"type": "do-nothing"}],
}

EXAMPLES = {
    "deployment-event": DEPLOYMENT_EVENT_EXAMPLE,
    "notification": NOTIFICATION_EXAMPLE,
    "proactive": PROACTIVE_EXAMPLE,
}


def load_from_file(path: Path) -> Any:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        return json.loads(text)
    if suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("PyYAML is required to read YAML files; install pyyaml or use JSON input.")
        return yaml.safe_load(text)
    raise ValueError("File extension must be .json, .yaml, or .yml")


def load_from_stdin(input_format: str) -> Any:
    text = sys.stdin.read()
    if not text.strip():
        raise ValueError("No input was provided on stdin")
    if input_format == "json":
        return json.loads(text)
    if yaml is None:
        raise RuntimeError("PyYAML is required to read YAML from stdin; install pyyaml or use --stdin-format json.")
    return yaml.safe_load(text)


def normalize_automations(data: Any) -> list[Any]:
    if isinstance(data, dict) and "automations" in data:
        automations = data["automations"]
        if not isinstance(automations, list):
            raise ValueError("The 'automations' field must be a list")
        return automations
    if isinstance(data, list):
        return data
    return [data]


def validate_automations(data: Any) -> tuple[list[dict[str, Any]], list[tuple[int, str, str]]]:
    from pydantic import ValidationError
    from prefect.events.schemas.automations import AutomationCore

    valid: list[dict[str, Any]] = []
    failures: list[tuple[int, str, str]] = []
    for index, item in enumerate(normalize_automations(data)):
        name = item.get("name", f"automation at index {index}") if isinstance(item, dict) else f"automation at index {index}"
        try:
            automation = AutomationCore.model_validate(item)
        except ValidationError as exc:
            failures.append((index, str(name), exc.json(indent=2)))
        except Exception as exc:  # pragma: no cover - defensive for Prefect model changes
            failures.append((index, str(name), str(exc)))
        else:
            valid.append(automation.model_dump(mode="json"))
    return valid, failures


def print_summary(valid: list[dict[str, Any]], failures: list[tuple[int, str, str]], verbose: bool) -> int:
    for automation in valid:
        trigger = automation.get("trigger", {})
        actions = automation.get("actions", [])
        print(
            "OK: "
            f"{automation.get('name')} "
            f"trigger={trigger.get('type', 'event')} "
            f"actions={len(actions)} "
            f"enabled={automation.get('enabled')}"
        )
        if verbose:
            print(json.dumps(automation, indent=2, sort_keys=True))

    for index, name, error in failures:
        print(f"FAIL: index={index} name={name}", file=sys.stderr)
        print(error, file=sys.stderr)

    print(
        json.dumps(
            {
                "valid": len(valid),
                "failed": len(failures),
                "ok": not failures,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 1 if failures else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Prefect automation JSON/YAML locally with Prefect's AutomationCore model.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", type=Path, help="Path to a .json, .yaml, or .yml automation file.")
    source.add_argument("--json", help="Automation JSON string.")
    source.add_argument("--stdin", action="store_true", help="Read automation payload from stdin.")
    source.add_argument(
        "--example",
        choices=sorted(EXAMPLES),
        help="Print a built-in example payload and exit.",
    )
    parser.add_argument(
        "--stdin-format",
        choices=["json", "yaml"],
        default="json",
        help="Input format for --stdin. Default: json.",
    )
    parser.add_argument(
        "--wrap-list",
        action="store_true",
        help="When printing --example, wrap it as {'automations': [...]}.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print normalized automation JSON for each valid payload.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.example:
        payload: Any = EXAMPLES[args.example]
        if args.wrap_list:
            payload = {"automations": [payload]}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    try:
        if args.file:
            data = load_from_file(args.file)
        elif args.json:
            data = json.loads(args.json)
        elif args.stdin:
            data = load_from_stdin(args.stdin_format)
        else:  # pragma: no cover - argparse enforces this
            parser.error("one input source is required")
    except Exception as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2

    try:
        valid, failures = validate_automations(data)
    except Exception as exc:
        print(f"Validation setup error: {exc}", file=sys.stderr)
        return 2
    return print_summary(valid, failures, args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
