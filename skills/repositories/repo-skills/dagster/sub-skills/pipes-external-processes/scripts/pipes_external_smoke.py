#!/usr/bin/env python3
"""Safe smoke checks for external-side Dagster Pipes behavior.

This script intentionally does not launch Dagster, connect to cloud services, or require
credentials. It can demonstrate the inactive open_dagster_pipes behavior and the JSON
message shape expected from a non-Python process.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from collections.abc import Sequence
from typing import Any

PIPES_PROTOCOL_VERSION = "0.1"


def build_custom_message(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "__dagster_pipes_version": PIPES_PROTOCOL_VERSION,
        "method": "report_custom_message",
        "params": {"payload": payload},
    }


def run_inactive_demo() -> int:
    try:
        from dagster_pipes import open_dagster_pipes
    except ModuleNotFoundError as exc:
        print(
            "dagster_pipes is not importable. Install dagster-pipes in the external "
            "process environment before using open_dagster_pipes.",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with open_dagster_pipes() as pipes:
            pipes.log.info("inactive smoke log")
            pipes.report_custom_message({"status": "inactive-demo"})

    warning_messages = [str(item.message) for item in caught]
    print(
        json.dumps(
            {
                "opened_without_dagster": True,
                "warning_count": len(warning_messages),
                "warnings": warning_messages,
                "custom_message_shape": build_custom_message({"status": "inactive-demo"}),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def emit_json_message() -> int:
    print(json.dumps(build_custom_message({"status": "ok", "source": "smoke"}), sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safe Dagster Pipes external-process smoke helper",
    )
    parser.add_argument(
        "--inactive-demo",
        action="store_true",
        help="Import dagster_pipes and demonstrate no-op behavior when no Dagster bootstrap params exist.",
    )
    parser.add_argument(
        "--emit-json-message",
        action="store_true",
        help="Print a single JSON-line report_custom_message payload for non-Python protocol checks.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    selected = [args.inactive_demo, args.emit_json_message]
    if sum(bool(value) for value in selected) > 1:
        parser.error("choose only one smoke action")

    if args.inactive_demo:
        return run_inactive_demo()
    if args.emit_json_message:
        return emit_json_message()

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
