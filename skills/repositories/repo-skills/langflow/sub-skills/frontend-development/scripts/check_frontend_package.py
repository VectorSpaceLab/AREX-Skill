#!/usr/bin/env python3
"""Statically validate Langflow frontend package.json scripts.

This helper intentionally does not execute Node, npm, Vite, Jest, or
Playwright. It only reads package.json and reports whether the expected script
surface for Langflow frontend development is present.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_SCRIPTS = ("start", "build", "test")
QUALITY_SCRIPT_GROUPS = (
    ("lint", "lint:types", "lint:changed", "lint:types:changed"),
    ("check-format", "format"),
    ("type-check",),
)
COMMON_OPTIONAL_SCRIPTS = (
    "serve",
    "test:coverage",
    "test:watch",
    "format",
    "lint",
    "check-format",
    "type-check",
)


def load_package_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"package.json not found: {path}")
    if not path.is_file():
        raise ValueError(f"package.json path is not a file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"expected top-level JSON object in {path}")
    return data


def validate_scripts(package: dict[str, Any], strict: bool) -> tuple[list[str], list[str]]:
    scripts = package.get("scripts")
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(scripts, dict):
        return ["missing or invalid 'scripts' object"], warnings

    missing_required = [name for name in REQUIRED_SCRIPTS if name not in scripts]
    if missing_required:
        errors.append(f"missing required scripts: {', '.join(missing_required)}")

    for group in QUALITY_SCRIPT_GROUPS:
        if not any(name in scripts for name in group):
            labels = "/".join(group)
            errors.append(f"missing quality-gate script group: {labels}")

    missing_optional = [name for name in COMMON_OPTIONAL_SCRIPTS if name not in scripts]
    if missing_optional:
        message = f"optional common scripts absent: {', '.join(missing_optional)}"
        if strict:
            errors.append(message)
        else:
            warnings.append(message)

    for name, command in sorted(scripts.items()):
        if not isinstance(command, str) or not command.strip():
            errors.append(f"script '{name}' must be a non-empty string")

    return errors, warnings


def validate_engines(package: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    engines = package.get("engines")
    if not isinstance(engines, dict):
        warnings.append("missing engines object; expected a Node.js version constraint")
        return warnings
    node_constraint = engines.get("node")
    if not isinstance(node_constraint, str) or not node_constraint.strip():
        warnings.append("missing engines.node constraint")
    elif "20.19" not in node_constraint and ">=20" not in node_constraint and ">= 20" not in node_constraint:
        warnings.append(
            "engines.node does not clearly state the Langflow frontend minimum of Node >=20.19.0"
        )
    return warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check that a Langflow frontend package.json exposes expected npm scripts without running Node.",
    )
    parser.add_argument(
        "package_json",
        nargs="?",
        default="src/frontend/package.json",
        help="Path to package.json. Defaults to src/frontend/package.json from the current working directory.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat missing common optional scripts as errors instead of warnings.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    package_path = Path(args.package_json)

    try:
        package = load_package_json(package_path)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    errors, warnings = validate_scripts(package, strict=args.strict)
    warnings.extend(validate_engines(package))

    package_name = package.get("name", "<unknown>")
    package_version = package.get("version", "<unknown>")
    print(f"Checked {package_path} ({package_name} {package_version})")

    scripts = package.get("scripts") if isinstance(package.get("scripts"), dict) else {}
    present_scripts = ", ".join(sorted(scripts)) if scripts else "<none>"
    print(f"Scripts present: {present_scripts}")

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("OK: frontend package script surface looks usable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
