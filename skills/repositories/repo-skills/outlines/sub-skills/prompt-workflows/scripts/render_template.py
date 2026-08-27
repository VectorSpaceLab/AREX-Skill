#!/usr/bin/env python3
"""Render a prompt with outlines.Template.

This script is intentionally local-only:
- it renders an inline Jinja template or a bundled literal fixture,
- it accepts template variables as JSON,
- it does not call providers,
- it does not read repository-relative prompt files by default,
- it does not execute generated code.
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from typing import Any, Dict

from outlines import Template


FIXTURES: Dict[str, Dict[str, Any]] = {
    "event": {
        "description": "Event extraction prompt with time context.",
        "template": textwrap.dedent(
            """
            Current time: {{ now }}
            Message: {{ message }}
            Extract title, location, and start time.
            """
        ).strip(),
        "vars": {
            "now": "Friday 10 May 2024 09:30",
            "message": "Move the design review to Tuesday at 3pm in Studio 4.",
        },
    },
    "consensus": {
        "description": "Self-consistency prompt for repeated reasoning.",
        "template": textwrap.dedent(
            """
            Solve the problem carefully and return only the final answer.

            Problem: {{ question }}
            """
        ).strip(),
        "vars": {
            "question": "If a train leaves at 6 and arrives at 9, how many hours did it travel?",
        },
    },
    "loop-task": {
        "description": "BabyAGI-style bounded task loop prompt.",
        "template": textwrap.dedent(
            """
            Objective: {{ objective }}
            Task: {{ task }}
            Return a concise result and, if useful, a short list of follow-up tasks.
            """
        ).strip(),
        "vars": {
            "objective": "Build a reliable note triage workflow.",
            "task": "Summarize the latest customer messages.",
        },
    },
    "phone-debug": {
        "description": "Regex iteration prompt for structured output debugging.",
        "template": textwrap.dedent(
            """
            Generate one phone number that matches this format:
            {{ pattern }}
            """
        ).strip(),
        "vars": {
            "pattern": r"\([0-9]{3}\) [0-9]{3}-[0-9]{4}",
        },
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render an Outlines Template from inline text or a bundled fixture.",
    )
    parser.add_argument(
        "--list-fixtures",
        action="store_true",
        help="List bundled fixtures and exit.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--template",
        help="Inline Jinja template text to render.",
    )
    group.add_argument(
        "--fixture",
        choices=sorted(FIXTURES.keys()),
        help="Render one of the bundled literal fixtures.",
    )
    parser.add_argument(
        "--vars-json",
        default="{}",
        help='JSON object with template variables, e.g. "{\"name\": \"Ada\"}".',
    )
    return parser.parse_args()


def load_vars(raw: str) -> Dict[str, Any]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"--vars-json must be valid JSON: {exc.msg}") from exc

    if not isinstance(parsed, dict):
        raise ValueError("--vars-json must decode to a JSON object.")

    return parsed


def render(template_text: str, variables: Dict[str, Any]) -> str:
    template = Template.from_string(template_text, filters={})
    return template(**variables)


def print_fixtures() -> None:
    for name in sorted(FIXTURES):
        info = FIXTURES[name]
        print(f"{name}: {info['description']}")


def main() -> int:
    args = parse_args()

    if args.list_fixtures:
        print_fixtures()
        return 0

    if not args.template and not args.fixture:
        print(
            "error: provide either --template or --fixture (or use --list-fixtures)",
            file=sys.stderr,
        )
        return 2

    try:
        if args.fixture:
            fixture = FIXTURES[args.fixture]
            template_text = fixture["template"]
            variables = dict(fixture["vars"])
            variables.update(load_vars(args.vars_json))
        else:
            template_text = args.template
            variables = load_vars(args.vars_json)

        rendered = render(template_text, variables)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
