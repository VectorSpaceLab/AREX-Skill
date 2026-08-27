#!/usr/bin/env python3
"""Print ContextForge validation commands for selected change areas.

This script does not execute commands. It helps choose a bounded validation set.

Examples:
  python contextforge_validation_plan.py --areas python auth
  python contextforge_validation_plan.py --areas transport rust --format markdown
"""
from __future__ import annotations

import argparse
import json
from collections import OrderedDict

COMMANDS: dict[str, list[str]] = {
    "python": [
        "make autoflake isort black pre-commit",
        "make ruff bandit interrogate pylint verify",
        "make doctest test htmlcov",
    ],
    "auth": [
        "pytest -k 'auth or rbac or token_scoping' tests/unit/mcpgateway -q",
        "make test-mcp-rbac  # requires live gateway",
        "make detect-secrets-scan",
    ],
    "security": [
        "make bandit",
        "make detect-secrets-scan",
        "pytest -k 'security or csrf or token or rbac' tests/unit tests/security -q",
    ],
    "transport": [
        "make testing-up  # or the rust/python mode-specific rebuild target",
        "make test-mcp-protocol-e2e",
        "make test-mcp-rbac",
        "make test-mcp-access-matrix",
    ],
    "rust": [
        "make -C crates/mcp_runtime fmt-check clippy-all test test-rmcp",
        "make testing-rebuild-rust-full",
        "make test-mcp-protocol-e2e test-mcp-rbac test-mcp-access-matrix test-mcp-session-isolation",
        "cargo test --release --manifest-path crates/mcp_runtime/Cargo.toml",
    ],
    "ui": [
        "make build-ui",
        "npx vitest run",
        "make lint-web",
        "make test-ui-smoke",
    ],
    "docs": [
        "cd docs && make build",
    ],
    "helm": [
        "make -C charts/mcp-stack lint",
        "make -C charts/mcp-stack lint-values",
        "make -C charts/mcp-stack validate-all",
        "make -C charts/mcp-stack test-template",
    ],
    "plugin": [
        "pytest tests/unit/mcpgateway/plugins -q",
        "PLUGINS_CONFIG_FILE=plugins/plugin_parity_config.yaml make test-mcp-plugin-parity  # requires live gateway",
    ],
    "migration": [
        "cd mcpgateway && alembic heads",
        "pytest tests/migration tests/unit/mcpgateway -k migration -q",
        "make test",
    ],
}

NOTES: dict[str, list[str]] = {
    "auth": ["Add deny-path tests for unauthenticated, wrong-team/public-only, insufficient-permission, and disabled-feature cases."],
    "transport": ["Check /health x-contextforge-mcp-runtime-mode and x-contextforge-mcp-transport-mounted before interpreting live test failures."],
    "rust": ["Choose Python baseline, rust shadow, rust edge, or rust full intentionally; do not assume the mounted transport."],
    "ui": ["Rebuild the Admin UI bundle after JS/CSS/template changes."],
    "migration": ["Verify one Alembic head before and after; snapshot settings into migration_metadata when downgrade uses runtime config."],
    "helm": ["Helm install/upgrade commands require explicit cluster context and are not included in this no-execute plan."],
    "plugin": ["Use config lint/unit tests before live plugin parity unless public MCP hook integration changed."],
}


def unique_commands(areas: list[str]) -> list[str]:
    ordered: OrderedDict[str, None] = OrderedDict()
    for area in areas:
        for command in COMMANDS[area]:
            ordered.setdefault(command, None)
    return list(ordered)


def main() -> int:
    parser = argparse.ArgumentParser(description="Print ContextForge validation commands for change areas without executing them.")
    parser.add_argument("--areas", nargs="+", choices=sorted(COMMANDS), required=True, help="Change areas to plan for.")
    parser.add_argument("--format", choices=["text", "markdown", "json"], default="text")
    args = parser.parse_args()

    commands = unique_commands(args.areas)
    notes = [note for area in args.areas for note in NOTES.get(area, [])]
    result = {"areas": args.areas, "commands": commands, "notes": notes}

    if args.format == "json":
        print(json.dumps(result, indent=2))
    elif args.format == "markdown":
        print("# ContextForge Validation Plan\n")
        print("## Areas\n")
        for area in args.areas:
            print(f"- `{area}`")
        print("\n## Commands\n")
        for command in commands:
            print(f"- `{command}`")
        if notes:
            print("\n## Notes\n")
            for note in notes:
                print(f"- {note}")
    else:
        print("Areas: " + ", ".join(args.areas))
        print("Commands:")
        for command in commands:
            print(f"  {command}")
        if notes:
            print("Notes:")
            for note in notes:
                print(f"  - {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
