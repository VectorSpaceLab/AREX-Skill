#!/usr/bin/env python3
"""Run a small, offline LEANN installation and registry probe.

The probe deliberately avoids model downloads, network calls, index creation,
daemon startup, and provider calls. It is suitable as a first check before
running one of the task-specific smoke scripts in this skill.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import sys
from typing import Any


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-cli",
        action="store_true",
        help="construct the public CLI parser without executing a command",
    )
    parser.add_argument(
        "--require-backend",
        action="append",
        default=[],
        metavar="NAME",
        help="require a named backend registry entry (repeatable)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the result as JSON instead of human-readable lines",
    )
    return parser.parse_args(argv)


def distribution_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def run(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    result: dict[str, Any] = {
        "python": sys.version.split()[0],
        "import": False,
        "cli_parser": None,
        "backends": [],
        "distribution_versions": {
            name: distribution_version(name)
            for name in ("leann", "leann-core", "leann-backend-hnsw", "leann-backend-ivf", "leann-backend-diskann")
        },
        "errors": [],
    }
    try:
        leann = importlib.import_module("leann")
        result["import"] = True
    except Exception as exc:  # report the actionable import failure, then exit nonzero
        result["errors"].append(f"import leann: {type(exc).__name__}: {exc}")
        return 1, result

    registry = getattr(leann, "BACKEND_REGISTRY", None)
    if registry is not None:
        try:
            result["backends"] = sorted(str(name) for name in registry)
        except Exception as exc:
            result["errors"].append(f"read backend registry: {type(exc).__name__}: {exc}")

    for name in args.require_backend:
        if name not in result["backends"]:
            result["errors"].append(
                f"required backend {name!r} is not present in the discovered registry"
            )

    if args.check_cli:
        try:
            cli_module = importlib.import_module("leann.cli")
            cli = cli_module.LeannCLI()
            cli.create_parser()
            result["cli_parser"] = True
        except Exception as exc:
            result["cli_parser"] = False
            result["errors"].append(f"construct CLI parser: {type(exc).__name__}: {exc}")

    return (1 if result["errors"] else 0), result


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    code, result = run(args)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Python: {result['python']}")
        print(f"LEANN import: {'OK' if result['import'] else 'FAILED'}")
        if result["cli_parser"] is not None:
            print(f"CLI parser: {'OK' if result['cli_parser'] else 'FAILED'}")
        print("Backends: " + (", ".join(result["backends"]) or "none discovered"))
        for error in result["errors"]:
            print(f"ERROR: {error}", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
