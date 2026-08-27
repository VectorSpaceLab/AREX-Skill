#!/usr/bin/env python3
"""Strictly check OpenQASM 3 parser acceptance with the public openqasm3 API."""

from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
from pathlib import Path
import sys
from typing import Any, Optional, Sequence, Tuple


EXIT_OK = 0
EXIT_INPUT = 2
EXIT_DEPENDENCY = 3
EXIT_REJECTED = 4
EXIT_INTERNAL = 5

SCOPE_NOTICE = (
    "Parser acceptance only: semantic/type validation, include resolution, "
    "compiler validation, and provider execution were not performed."
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check one OpenQASM 3 source with strict public openqasm3 parsing. "
            "Use a path, --source, '-' for stdin, or no input selector for stdin."
        ),
        epilog=(
            "Exit codes: 0 accepted; 2 usage/input error; 3 parser dependency "
            "error; 4 parser rejection; 5 unexpected parser/printer error.\n"
            "Success is not semantic/type/include/compiler/provider validation."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="UTF-8 OpenQASM file, or '-' to read stdin (default: stdin)",
    )
    parser.add_argument(
        "--source",
        metavar="TEXT",
        help="OpenQASM source text supplied directly; cannot be combined with path",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="emit one JSON diagnostic object",
    )
    parser.add_argument(
        "--normalized",
        action="store_true",
        help="on success, include source emitted by openqasm3.dumps",
    )
    return parser


def _display(value: Any) -> str:
    if value is None:
        return "none"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def emit(result: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return

    print(f"status: {_display(result.get('status'))}")
    if "accepted" in result:
        print(f"accepted: {_display(result.get('accepted'))}")
    input_info = result.get("input") or {}
    if input_info:
        print(f"input_kind: {_display(input_info.get('kind'))}")
        print(f"input_label: {_display(input_info.get('label'))}")
        print(f"source_characters: {_display(input_info.get('characters'))}")
    if "package_version" in result:
        print(f"openqasm3_version: {_display(result.get('package_version'))}")
    if "supported_versions" in result:
        print(
            "supported_versions: "
            + ", ".join(result.get("supported_versions") or [])
        )
    version = result.get("version") or {}
    if version:
        detected = version.get("detected")
        detected_text = tuple(detected) if detected is not None else None
        print(f"detected_version: {_display(detected_text)}")
        print(f"header_version: {_display(version.get('header'))}")
        print(f"ast_version: {_display(version.get('ast'))}")
    if "statement_count" in result:
        print(f"statement_count: {_display(result.get('statement_count'))}")
    diagnostic = result.get("diagnostic") or {}
    if diagnostic:
        print(f"exception: {_display(diagnostic.get('exception'))}")
        print(f"message: {_display(diagnostic.get('message'))}")
        print(f"line: {_display(diagnostic.get('line'))}")
        print(f"column: {_display(diagnostic.get('column'))}")
        parser_stderr = diagnostic.get("parser_stderr")
        if parser_stderr:
            print("parser_stderr:")
            print(parser_stderr.rstrip("\n"))
    print(f"validation_scope: {result.get('validation_scope', SCOPE_NOTICE)}")
    if "normalized_source" in result:
        print("normalized_source:")
        normalized = result["normalized_source"]
        sys.stdout.write(normalized)
        if normalized and not normalized.endswith("\n"):
            print()


def read_source(args: argparse.Namespace) -> Tuple[str, dict[str, Any]]:
    if args.path is not None and args.source is not None:
        raise ValueError("supply exactly one of path, --source, or stdin")

    if args.source is not None:
        source = args.source
        return source, {
            "kind": "literal",
            "label": "--source",
            "characters": len(source),
        }

    if args.path is None or args.path == "-":
        source = sys.stdin.read()
        return source, {
            "kind": "stdin",
            "label": "stdin",
            "characters": len(source),
        }

    path = Path(args.path).expanduser()
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"cannot read UTF-8 input '{path}': {exc}") from exc
    return source, {
        "kind": "path",
        "label": str(path),
        "characters": len(source),
    }


def load_openqasm3() -> Tuple[Any, Any, Any, Any, str, list[str]]:
    try:
        package = importlib.import_module("openqasm3")
    except (ImportError, ModuleNotFoundError) as exc:
        raise ImportError(
            "cannot import openqasm3; install the package with its parser extra, "
            "for example: python -m pip install 'openqasm3[parser]'"
        ) from exc

    try:
        parser_module = importlib.import_module("openqasm3.parser")
    except (ImportError, ModuleNotFoundError) as exc:
        raise ImportError(
            "cannot import openqasm3.parser; install 'openqasm3[parser]' and "
            "ensure the antlr4-python3-runtime version has a matching generated parser: "
            f"{exc}"
        ) from exc

    required = ("parse", "parse_version", "QASM3ParsingError")
    missing = [name for name in required if not hasattr(parser_module, name)]
    if missing or not hasattr(package, "dumps"):
        detail = ", ".join(missing + ([] if hasattr(package, "dumps") else ["dumps"]))
        raise ImportError(f"installed openqasm3 lacks required public API(s): {detail}")

    try:
        spec_module = importlib.import_module("openqasm3.spec")
        supported = list(getattr(spec_module, "supported_versions", []))
    except (ImportError, ModuleNotFoundError):
        supported = []

    package_version = str(getattr(package, "__version__", "unknown"))
    return (
        parser_module.parse,
        parser_module.parse_version,
        parser_module.QASM3ParsingError,
        package.dumps,
        package_version,
        supported,
    )


def dotted(parts: Optional[Sequence[int]]) -> Optional[str]:
    if parts is None:
        return None
    return ".".join(str(part) for part in parts)


def base_result(input_info: dict[str, Any]) -> dict[str, Any]:
    return {
        "tool": "check_syntax",
        "input": input_info,
        "validation_scope": SCOPE_NOTICE,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        source, input_info = read_source(args)
    except ValueError as exc:
        result = base_result({})
        result.update(
            {
                "status": "input-error",
                "accepted": False,
                "diagnostic": {
                    "exception": type(exc).__name__,
                    "message": str(exc),
                    "line": None,
                    "column": None,
                    "parser_stderr": None,
                },
            }
        )
        emit(result, as_json=args.as_json)
        return EXIT_INPUT

    result = base_result(input_info)

    try:
        parse, parse_version, parsing_error, dumps, package_version, supported = (
            load_openqasm3()
        )
    except ImportError as exc:
        result.update(
            {
                "status": "dependency-error",
                "accepted": False,
                "diagnostic": {
                    "exception": type(exc).__name__,
                    "message": str(exc),
                    "line": None,
                    "column": None,
                    "parser_stderr": None,
                },
            }
        )
        emit(result, as_json=args.as_json)
        return EXIT_DEPENDENCY

    result["package_version"] = package_version
    result["supported_versions"] = supported

    detected_parts: Optional[Tuple[int, ...]] = None
    parser_stderr = io.StringIO()
    try:
        detected_parts = parse_version(source)
        with contextlib.redirect_stderr(parser_stderr):
            program = parse(source, permissive=False, ignore_version=False)
    except parsing_error as exc:
        result.update(
            {
                "status": "rejected",
                "accepted": False,
                "version": {
                    "detected": (
                        list(detected_parts) if detected_parts is not None else None
                    ),
                    "header": dotted(detected_parts),
                    "ast": None,
                },
                "diagnostic": {
                    "exception": type(exc).__name__,
                    "message": str(exc),
                    "line": getattr(exc, "line", None),
                    "column": getattr(exc, "column", None),
                    "parser_stderr": parser_stderr.getvalue() or None,
                },
            }
        )
        emit(result, as_json=args.as_json)
        return EXIT_REJECTED
    except Exception as exc:  # Defensive: distinguish tool/runtime faults from rejection.
        result.update(
            {
                "status": "internal-error",
                "accepted": False,
                "version": {
                    "detected": (
                        list(detected_parts) if detected_parts is not None else None
                    ),
                    "header": dotted(detected_parts),
                    "ast": None,
                },
                "diagnostic": {
                    "exception": type(exc).__name__,
                    "message": str(exc),
                    "line": getattr(exc, "line", None),
                    "column": getattr(exc, "column", None),
                    "parser_stderr": parser_stderr.getvalue() or None,
                },
            }
        )
        emit(result, as_json=args.as_json)
        return EXIT_INTERNAL

    result.update(
        {
            "status": "accepted",
            "accepted": True,
            "version": {
                "detected": list(detected_parts) if detected_parts is not None else None,
                "header": dotted(detected_parts),
                "ast": getattr(program, "version", None),
            },
            "statement_count": len(getattr(program, "statements", [])),
        }
    )
    if parser_stderr.getvalue():
        result["diagnostic"] = {
            "exception": None,
            "message": "parser emitted stderr despite returning a Program",
            "line": None,
            "column": None,
            "parser_stderr": parser_stderr.getvalue(),
        }

    if args.normalized:
        try:
            result["normalized_source"] = dumps(program)
        except Exception as exc:  # Printing is optional but requested output must be reliable.
            result.update(
                {
                    "status": "normalization-error",
                    "diagnostic": {
                        "exception": type(exc).__name__,
                        "message": str(exc),
                        "line": None,
                        "column": None,
                        "parser_stderr": None,
                    },
                }
            )
            emit(result, as_json=args.as_json)
            return EXIT_INTERNAL

    emit(result, as_json=args.as_json)
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
