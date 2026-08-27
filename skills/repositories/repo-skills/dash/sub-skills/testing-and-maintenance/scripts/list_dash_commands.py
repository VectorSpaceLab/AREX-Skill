#!/usr/bin/env python3
"""Print a curated Dash command catalog for testing/build/maintenance tasks."""

from __future__ import annotations

import argparse
import json

COMMANDS = {
    "setup": [
        "python -m pip install -e \".[testing]\"",
        "python -m pip install \"dash[fastapi]\"",
        "python -m pip install \"dash[quart]\"",
        "python -m pip install \"dash[diskcache]\"",
    ],
    "build": [
        "npm ci",
        "npm run build",
        "npm run first-build",
        "npm run setup-tests.py",
        "dash-update-components \"dash-core-components\"",
        "dash-update-components \"all\"",
    ],
    "lint": [
        "npm run lint",
        "npm run private::lint.black",
        "npm run private::lint.flake8",
        "npm run private::lint.pylint-dash",
        "npm run private::lint.renderer",
    ],
    "test": [
        "python -m pytest tests/unit/test_callback_unit.py -q",
        "python -m pytest tests/unit/test_layout.py -q",
        "python -m pytest tests/unit/test_configs.py -q",
        "python -m pytest tests/unit/test_resources.py -q",
        "python -m pytest tests/backend_tests/test_preconfig_backends.py -q",
        "python -m pytest tests/integration/callbacks/test_basic_callback.py -q --headless -xvs",
    ],
    "component": [
        "dash-generate-components --help",
        "dash-update-components --help",
        "renderer --help",
    ],
    "renderer": [
        "cd dash/dash-renderer && npm run test",
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a curated Dash command catalog.")
    parser.add_argument("--category", choices=["setup", "build", "lint", "test", "component", "renderer", "all"], default="all")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.category == "all":
        payload = COMMANDS
    else:
        payload = {args.category: COMMANDS[args.category]}

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for category, commands in payload.items():
            print(category + ":")
            for command in commands:
                print(f"  - {command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
