#!/usr/bin/env python3
"""Validate Cognee typed memory payload JSON without writing memory.

Examples:
  python check_agent_memory_payloads.py --type qa --payload '{"question":"q","answer":"a"}'
  python check_agent_memory_payloads.py --type trace --payload '{"origin_function":"tool"}'
"""

from __future__ import annotations

import argparse
import json
from typing import Any


def load_payload(raw: str) -> dict[str, Any]:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("payload must be a JSON object")
    return value


def model_for(kind: str):
    from cognee.memory import QAEntry, TraceEntry, FeedbackEntry, SkillRunEntry

    return {
        "qa": QAEntry,
        "trace": TraceEntry,
        "feedback": FeedbackEntry,
        "skill_run": SkillRunEntry,
    }[kind]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Cognee typed memory payload.")
    parser.add_argument(
        "--type",
        choices=["qa", "trace", "feedback", "skill_run"],
        required=True,
        help="Memory entry type to validate",
    )
    parser.add_argument("--payload", required=True, help="JSON object payload without the type field")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print normalized JSON")
    args = parser.parse_args()

    payload = load_payload(args.payload)
    cls = model_for(args.type)
    entry = cls.model_validate({"type": args.type, **payload})
    data = entry.model_dump(mode="json")
    if args.pretty:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(json.dumps(data, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
