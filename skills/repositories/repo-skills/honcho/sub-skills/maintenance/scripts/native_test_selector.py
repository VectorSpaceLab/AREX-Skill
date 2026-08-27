#!/usr/bin/env python3
"""Suggest safe Honcho maintenance checks from changed paths.

This helper does not run tests. It prints a conservative command matrix so a
maintainer can choose a narrow validation path first.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


RULES: list[dict[str, Any]] = [
    {
        "match": "src/routers/",
        "commands": [
            "uv run pytest tests/routes/",
            "uv run pytest tests/routes/test_auth_route_policy.py",
            "uv run pytest tests/routes/test_scope_route_policy.py",
        ],
    },
    {
        "match": "src/config.py",
        "commands": [
            "uv run pytest tests/test_config.py",
            "uv run pytest tests/startup/test_embedding_validator.py",
            "uv run pytest tests/llm/test_model_config.py",
        ],
    },
    {
        "match": "src/llm/",
        "commands": [
            "uv run pytest tests/llm/",
            "uv run pytest tests/dialectic/",
            "uv run pytest tests/dreamer/",
        ],
    },
    {
        "match": "sdks/python/",
        "commands": [
            "uv run pytest tests/sdk/",
            "uv run pytest tests/sdk/sdk_integration_test.py",
        ],
    },
    {
        "match": "sdks/typescript/",
        "commands": [
            "uv run pytest tests/ -k typescript",
            "cd sdks/typescript && bun run tsc --noEmit",
        ],
    },
    {
        "match": "scripts/configure_embeddings.py",
        "commands": [
            "uv run pytest tests/scripts/test_configure_embeddings.py",
            "uv run pytest tests/startup/test_embedding_validator.py",
        ],
    },
    {
        "match": "scripts/update_version.py",
        "commands": [
            "uv run pytest tests/test_generate_jwt_script.py",
            "uv run pytest tests/sdk/",
            "uv run pytest tests/sdk_typescript/",
        ],
    },
]


def _select(paths: list[str]) -> dict[str, Any]:
    selected: list[dict[str, Any]] = []
    for rule in RULES:
        if any(rule["match"] in path for path in paths):
            selected.append(rule)
    if not selected:
        selected = [
            {
                "match": "default",
                "commands": [
                    "uv run pytest tests/",
                    "uv run basedpyright",
                    "uv run ruff check src/",
                ],
            }
        ]
    return {
        "input_paths": paths,
        "selected": selected,
        "notes": [
            "Use the narrowest command first.",
            "Escalate to broader suites only when the surface crosses boundaries.",
            "Treat live-provider and benchmark suites as gated or optional unless explicitly required.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Changed file paths")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    report = _select([str(Path(p)) for p in args.paths])
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for rule in report["selected"]:
            print(f"Match: {rule['match']}")
            for cmd in rule["commands"]:
                print(f"  {cmd}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
