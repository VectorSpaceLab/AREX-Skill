#!/usr/bin/env python3
"""Import a SMARTS agent module and report exact registry name/version presence.

This is a read-only checker. It never installs packages, calls an entry point,
constructs a policy, starts SMARTS/Ray, downloads a checkpoint, or trains.
It works from any current working directory when the target package is
importable by the selected Python interpreter.
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from typing import Any


LOCATOR_RE = re.compile(r"^(?:(?P<module>[^:]+):)?(?P<name>[\w:./-]+-(?:v\d+|latest))$")


def parse_locator(locator: str) -> tuple[str | None, str]:
    """Return (module, registered-name), or raise a useful ValueError."""
    match = LOCATOR_RE.fullmatch(locator)
    if not match:
        raise ValueError(
            "locator must be 'importable.module:agent-name-vN' "
            "or 'agent-name-vN'"
        )
    return match.group("module"), match.group("name")


def check_locator(locator: str) -> dict[str, Any]:
    """Import the requested module and inspect the SMARTS registry."""
    module_name, registered_name = parse_locator(locator)
    result: dict[str, Any] = {
        "locator": locator,
        "module": module_name,
        "registered_name": registered_name,
        "imported": False,
        "registered": False,
    }

    if module_name:
        try:
            importlib.import_module(module_name)
            result["imported"] = True
        except Exception as exc:  # report optional dependency/import errors
            result["error_type"] = type(exc).__name__
            result["error"] = str(exc)
            return result

    try:
        from smarts.zoo.registry import agent_registry
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        result["error"] = f"cannot import SMARTS registry: {exc}"
        return result

    factory = agent_registry.index.get(registered_name)
    if factory is None:
        result["error_type"] = "MissingRegistration"
        result["error"] = (
            f"module imported but registered name/version is absent: "
            f"{registered_name}"
        )
        result["available_names"] = sorted(agent_registry.index)
        return result

    result["registered"] = True
    result["factory_name"] = factory.name
    result["entry_point_type"] = type(factory.entrypoint).__name__
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import a SMARTS agent module and check a registered locator."
    )
    parser.add_argument(
        "--locator",
        required=True,
        help="module:agent-name-vN (or an already-registered agent-name-vN)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the result as JSON instead of a short status line",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = check_locator(args.locator)
    except ValueError as exc:
        result = {
            "locator": args.locator,
            "imported": False,
            "registered": False,
            "error_type": "InvalidLocator",
            "error": str(exc),
        }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif result["registered"]:
        print(f"OK: {args.locator} is registered")
    else:
        print(f"ERROR: {result.get('error', 'locator is not registered')}")
    return 0 if result["registered"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
