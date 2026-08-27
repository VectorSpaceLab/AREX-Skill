#!/usr/bin/env python3
"""Probe the public openqasm3 installation without using a repository checkout.

This helper is intentionally read-only: it reports package metadata, supported
specification versions, parser availability, public signatures, and a tiny
parse/print/reparse smoke result. It does not download packages or execute a
circuit.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from typing import Any, Optional, Sequence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check the public openqasm3 AST/parser/printer installation with a "
            "tiny CPU-only parse and print smoke test."
        )
    )
    parser.add_argument(
        "--json", action="store_true", dest="as_json", help="emit a JSON report"
    )
    parser.add_argument(
        "--source",
        default="OPENQASM 3.1; qubit q; bit c; c = measure q;",
        help="tiny source used for the smoke test",
    )
    return parser


def report_error(message: str, as_json: bool) -> int:
    result = {"status": "error", "message": message}
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"error: {message}", file=sys.stderr)
    return 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        package = importlib.import_module("openqasm3")
        spec = importlib.import_module("openqasm3.spec")
        parser_module = importlib.import_module("openqasm3.parser")
        version = getattr(package, "__version__", None)
        supported = list(getattr(spec, "supported_versions", []))
        parse = getattr(package, "parse")
        parse_version = getattr(package, "parse_version")
        dumps = getattr(package, "dumps")
        program = parse(args.source)
        normalized = dumps(program)
        reparsed = parse(normalized)
        result: dict[str, Any] = {
            "status": "ok",
            "package": "openqasm3",
            "package_version": version,
            "supported_versions": supported,
            "parser_module": parser_module.__name__,
            "signatures": {
                "parse": str(inspect.signature(parse)),
                "parse_version": str(inspect.signature(parse_version)),
                "dumps": str(inspect.signature(dumps)),
            },
            "smoke": {
                "detected_version": list(parse_version(args.source) or []) or None,
                "program_version": getattr(program, "version", None),
                "statement_count": len(getattr(program, "statements", [])),
                "normalized_reparse": type(reparsed).__name__ == "Program",
            },
            "scope": (
                "Import and parse/print/reparse only; no semantic compiler, "
                "include resolver, simulator, provider, or QPU validation."
            ),
        }
    except Exception as exc:  # keep missing optional parser dependencies actionable
        return report_error(
            f"openqasm3 parser smoke failed: {type(exc).__name__}: {exc}. "
            "Install the parser extra with: python -m pip install 'openqasm3[parser]'",
            args.as_json,
        )

    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"status: {result['status']}")
        print(f"package: {result['package']} {result['package_version']}")
        print("supported_versions: " + ", ".join(result["supported_versions"]))
        smoke = result["smoke"]
        print(f"detected_version: {smoke['detected_version']}")
        print(f"program_version: {smoke['program_version']}")
        print(f"statement_count: {smoke['statement_count']}")
        print(f"normalized_reparse: {smoke['normalized_reparse']}")
        print(result["scope"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
