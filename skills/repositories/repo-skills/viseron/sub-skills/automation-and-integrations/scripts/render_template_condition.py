#!/usr/bin/env python3
"""Render a Viseron-style Jinja template or condition locally.

This helper is intentionally offline: it reads JSON from arguments/files, builds a
small state/event context that mirrors Viseron's template helper, renders with
Jinja2, and prints the result. It does not import Viseron and does not contact
MQTT, HTTP, Telegram, Gotify, Discord, ONVIF, or any other network service.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


TRUTHY_STRINGS = {"1", "true", "yes", "on", "enable"}


class AttrDict(dict):
    """Dictionary with attribute access for nested event/state data."""

    def __getattr__(self, key: str) -> Any:
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc


class StateNamespace:
    """Mimic Viseron's state namespace: states.domain.object_id."""

    def __init__(self, states: dict[str, Any]) -> None:
        self._states = states

    def __getattr__(self, domain: str) -> "DomainNamespace":
        return DomainNamespace(self._states, domain)

    def __getitem__(self, key: str) -> Any:
        return self._states[key]


class DomainNamespace:
    """Resolve states.sensor.temperature to states['sensor.temperature']."""

    def __init__(self, states: dict[str, Any], domain: str) -> None:
        self._states = states
        self._domain = domain

    def __getattr__(self, entity: str) -> Any:
        key = f"{self._domain}.{entity}"
        return self._states[key]

    def __getitem__(self, entity: str) -> Any:
        key = f"{self._domain}.{entity}"
        return self._states[key]


def wrap(value: Any) -> Any:
    """Recursively wrap mappings so Jinja can use dot notation."""

    if isinstance(value, dict):
        return AttrDict({str(key): wrap(item) for key, item in value.items()})
    if isinstance(value, list):
        return [wrap(item) for item in value]
    return value


def read_text_arg(value: str | None, file_value: str | None, *, label: str) -> str:
    """Read either a direct string or a file path argument."""

    if value is not None and file_value is not None:
        raise ValueError(f"Provide either --{label} or --{label}-file, not both")
    if file_value is not None:
        if file_value == "-":
            return sys.stdin.read()
        return Path(file_value).read_text(encoding="utf-8")
    if value is not None:
        return value
    return ""


def parse_json_arg(value: str | None, file_value: str | None, *, label: str) -> Any:
    """Parse JSON from a direct argument or file path, defaulting to {}."""

    text = read_text_arg(value, file_value, label=label)
    if not text.strip():
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON for {label}: {exc}") from exc


def render_template(
    template_text: str,
    *,
    event: Any,
    states: dict[str, Any],
    strict_undefined: bool,
) -> str:
    """Render a Jinja template with Viseron-like variables."""

    try:
        from jinja2 import Environment, StrictUndefined
    except ImportError as exc:  # pragma: no cover - depends on target env
        raise RuntimeError(
            "Jinja2 is required to render templates. Install the package or run "
            "inside a Viseron-compatible Python environment."
        ) from exc

    env_kwargs: dict[str, Any] = {}
    if strict_undefined:
        env_kwargs["undefined"] = StrictUndefined
    env = Environment(autoescape=False, **env_kwargs)  # noqa: S701 - local renderer
    template = env.from_string(template_text)
    return template.render(states=StateNamespace(states), event=event)


def condition_bool(rendered: Any) -> bool:
    """Apply Viseron's current rendered-condition truthiness rules."""

    if rendered is None:
        return False
    if isinstance(rendered, bool):
        return rendered
    if isinstance(rendered, (int, float)) and not isinstance(rendered, bool):
        return rendered != 0

    text = str(rendered).strip()
    try:
        return float(text) > 0
    except (TypeError, ValueError):
        return text.lower() in TRUTHY_STRINGS


def sample_payload() -> dict[str, Any]:
    """Return sample event/state inputs for --sample."""

    return {
        "template": "{{ event.camera_identifier == 'front_door' and event.objects and (event.objects | selectattr('label', 'equalto', 'person') | list | length) > 0 }}",
        "event": {
            "camera_identifier": "front_door",
            "objects": [
                {
                    "label": "person",
                    "confidence": 0.91,
                    "rel_x1": 0.1,
                    "rel_y1": 0.2,
                    "rel_x2": 0.3,
                    "rel_y2": 0.7,
                }
            ],
            "zone": None,
        },
        "states": {
            "binary_sensor.front_door_motion_detected": {
                "state": "on",
                "attributes": {},
            },
            "sensor.front_door_operation_state": {
                "state": "recording",
                "attributes": {},
            },
        },
    }


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(
        description="Render a Viseron webhook Jinja template/condition offline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  render_template_condition.py --condition \
    --template '{{ event.motion_detected }}' \
    --event '{"camera_identifier":"front_door","motion_detected":true}'

  render_template_condition.py --template \
    'State is {{ states.binary_sensor.front_door_motion_detected.state }}' \
    --states '{"binary_sensor.front_door_motion_detected":{"state":"on"}}'

  render_template_condition.py --sample
""",
    )
    parser.add_argument("--template", help="Jinja template text to render.")
    parser.add_argument("--template-file", help="Read template text from this file.")
    parser.add_argument("--event", help="Event JSON object available as 'event'.")
    parser.add_argument("--event-file", help="Read event JSON from this file, or '-' for stdin.")
    parser.add_argument(
        "--states",
        help="States JSON mapping, keyed by entity_id, available as 'states'.",
    )
    parser.add_argument(
        "--states-file",
        help="Read states JSON from this file, or '-' for stdin.",
    )
    parser.add_argument(
        "--condition",
        action="store_true",
        help="Also evaluate the rendered text with Viseron's condition truthiness.",
    )
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Print a JSON object even when --condition is not set.",
    )
    parser.add_argument(
        "--fail-on-false",
        action="store_true",
        help="With --condition, exit 2 when the condition evaluates false.",
    )
    parser.add_argument(
        "--strict-undefined",
        action="store_true",
        help="Use Jinja StrictUndefined for missing event variables.",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Print sample template/event/states JSON and exit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.sample:
        print(json.dumps(sample_payload(), indent=2, sort_keys=True))
        return 0

    try:
        template_text = read_text_arg(
            args.template, args.template_file, label="template"
        )
        if not template_text:
            parser.error("--template or --template-file is required unless --sample is used")
        raw_event = parse_json_arg(args.event, args.event_file, label="event")
        raw_states = parse_json_arg(args.states, args.states_file, label="states")
        if not isinstance(raw_states, dict):
            raise ValueError("states JSON must be an object keyed by entity_id")

        event = wrap(raw_event)
        states = {str(key): wrap(value) for key, value in raw_states.items()}
        rendered = render_template(
            template_text,
            event=event,
            states=states,
            strict_undefined=args.strict_undefined,
        )
    except Exception as exc:  # pylint: disable=broad-except
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.condition:
        result = condition_bool(rendered)
        print(
            json.dumps(
                {
                    "condition": result,
                    "rendered": rendered,
                    "event_keys": sorted(raw_event.keys())
                    if isinstance(raw_event, dict)
                    else [],
                    "state_entity_ids": sorted(states.keys()),
                },
                indent=2,
                sort_keys=True,
            )
        )
        if args.fail_on_false and not result:
            return 2
        return 0

    if args.json_output:
        print(json.dumps({"rendered": rendered}, indent=2, sort_keys=True))
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
