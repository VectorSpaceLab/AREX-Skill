#!/usr/bin/env python3
"""Suggest focused Dash tests from a task description."""

from __future__ import annotations

import argparse
import json

SUGGESTIONS = [
    ("callback", ["python -m pytest tests/unit/test_callback_unit.py -q", "python -m pytest tests/integration/callbacks/test_basic_callback.py -q --headless -xvs"]),
    ("layout", ["python -m pytest tests/unit/test_layout.py -q"]),
    ("config", ["python -m pytest tests/unit/test_configs.py -q"]),
    ("resource", ["python -m pytest tests/unit/test_resources.py -q"]),
    ("backend", ["python -m pytest tests/backend_tests/test_preconfig_backends.py -q"]),
    ("async", ["python -m pytest tests/async_tests/test_async_callbacks.py -q"]),
    ("background", ["python -m pytest tests/background_callback/test_basic_long_callback001.py -q"]),
    ("websocket", ["python -m pytest tests/websocket/test_ws_basic.py -q"]),
    ("pages", ["python -m pytest tests/integration/multi_page/test_pages_layout.py -q --headless -xvs"]),
    ("clientside", ["python -m pytest tests/integration/clientside/test_clientside.py -q --headless -xvs"]),
    ("renderer", ["cd dash/dash-renderer && npm run test"]),
    ("component", ["dash-generate-components --help", "dash-update-components --help"]),
]


def suggest(text: str) -> list[str]:
    lowered = text.lower()
    result: list[str] = []
    for needle, commands in SUGGESTIONS:
        if needle in lowered:
            result.extend(commands)
    if not result:
        result = [
            "python -m pytest tests/unit/test_callback_unit.py -q",
            "python -m pytest tests/unit/test_layout.py -q",
            "python -m pytest tests/unit/test_configs.py -q",
        ]
    return list(dict.fromkeys(result))


def main() -> int:
    parser = argparse.ArgumentParser(description="Suggest focused Dash tests for a task description.")
    parser.add_argument("task", nargs="*", help="Free-text task description")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    text = " ".join(args.task)
    commands = suggest(text)
    payload = {"task": text, "commands": commands}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for command in commands:
            print(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
