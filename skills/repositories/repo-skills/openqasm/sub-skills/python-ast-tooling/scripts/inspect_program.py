#!/usr/bin/env python3
"""Inspect an OpenQASM 3 AST without relying on a repository checkout."""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional, Set, Tuple


class ToolError(RuntimeError):
    """A user-facing, non-traceback CLI error."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Parse OpenQASM 3 text and report its version, comments, AST node "
            "histogram, and source-span summary."
        )
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="input .qasm path; choose this, --source, or --stdin",
    )
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("--source", help="parse this source string")
    source_group.add_argument(
        "--stdin",
        action="store_true",
        help="read source from standard input",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit a machine-readable JSON report",
    )
    parser.add_argument(
        "--normalized-source",
        action="store_true",
        help="include printer-normalized source in the report",
    )
    parser.add_argument(
        "--permissive",
        action="store_true",
        help="allow parser recovery; recovered ASTs may be invalid",
    )
    parser.add_argument(
        "--ignore-version",
        action="store_true",
        help="bypass the supported-version gate (not a conformance check)",
    )
    return parser


def load_parser_api():
    try:
        import openqasm3  # type: ignore
    except ImportError as exc:
        raise ToolError(
            "openqasm3 parser components could not be imported. Install "
            "the parser extra with: python -m pip install 'openqasm3[parser]'. "
            f"Original error: {exc}"
        ) from exc

    if not hasattr(openqasm3, "parse") or not hasattr(openqasm3, "parse_version"):
        raise ToolError(
            "openqasm3 is installed, but its parser API is unavailable. Install "
            "the parser extra with: python -m pip install 'openqasm3[parser]'."
        )
    parser_module = getattr(openqasm3, "parser", None)
    if parser_module is None or not hasattr(parser_module, "get_comments"):
        raise ToolError(
            "this installed openqasm3 distribution lacks parser.get_comments, "
            "which this report requires. Package distributions with the same "
            "reported version can expose different APIs; select a compatible "
            "distribution and verify it with runtime introspection."
        )
    return openqasm3


def read_source(args: argparse.Namespace) -> Tuple[str, Optional[Path]]:
    choices = int(args.path is not None) + int(args.source is not None) + int(args.stdin)
    if choices != 1:
        raise ToolError("choose exactly one input: PATH, --source, or --stdin")

    if args.source is not None:
        return args.source, None
    if args.stdin:
        return sys.stdin.read(), None

    path = Path(args.path)
    try:
        return path.read_text(encoding="utf-8"), path
    except OSError as exc:
        raise ToolError(f"could not read input {path}: {exc}") from exc


def walk_nodes(value: Any, ast_module: Any, seen: Optional[Set[int]] = None) -> Iterator[Any]:
    """Yield every QASMNode, including nodes nested in tuple/list structures."""
    if seen is None:
        seen = set()
    if isinstance(value, ast_module.QASMNode):
        marker = id(value)
        if marker in seen:
            return
        seen.add(marker)
        yield value
        for child in vars(value).values():
            yield from walk_nodes(child, ast_module, seen)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from walk_nodes(child, ast_module, seen)
    elif isinstance(value, dict):
        for child in value.values():
            yield from walk_nodes(child, ast_module, seen)


def span_report(nodes: Iterable[Any]) -> Dict[str, Any]:
    nodes = list(nodes)
    spans = [node.span for node in nodes if getattr(node, "span", None) is not None]
    report: Dict[str, Any] = {
        "total_nodes": len(nodes),
        "nodes_with_span": len(spans),
        "nodes_without_span": len(nodes) - len(spans),
    }
    if spans:
        first = min((span.start_line, span.start_column) for span in spans)
        last = max((span.end_line, span.end_column) for span in spans)
        report["start"] = {"line": first[0], "column": first[1]}
        report["end"] = {"line": last[0], "column": last[1]}
    else:
        report["start"] = None
        report["end"] = None
    return report


def make_report(source: str, openqasm3: Any, args: argparse.Namespace) -> Dict[str, Any]:
    try:
        program = openqasm3.parse(
            source,
            permissive=args.permissive,
            ignore_version=args.ignore_version,
        )
    except Exception as exc:  # parser and contextual AST-generation errors share a public path
        line = getattr(exc, "line", None)
        column = getattr(exc, "column", None)
        location = ""
        if line is not None and column is not None:
            location = f" at line {line}, column {column}"
        elif line is not None:
            location = f" at line {line}"
        raise ToolError(f"OpenQASM parsing failed{location}: {exc}") from exc

    nodes = list(walk_nodes(program, openqasm3.ast))
    histogram = collections.Counter(type(node).__name__ for node in nodes)
    result: Dict[str, Any] = {
        "package_version": getattr(openqasm3, "__version__", None),
        "program_version": program.version,
        "parse_version": list(openqasm3.parse_version(source) or []) or None,
        "comments": openqasm3.parser.get_comments(source),
        "node_histogram": dict(sorted(histogram.items())),
        "span_summary": span_report(nodes),
    }
    if args.normalized_source:
        try:
            result["normalized_source"] = openqasm3.dumps(program)
        except Exception as exc:
            raise ToolError(f"AST parsed, but normalized printing failed: {exc}") from exc
    return result


def print_human(report: Dict[str, Any]) -> None:
    print(f"package version: {report['package_version']}")
    print(f"program version: {report['program_version'] or '(no header)'}")
    print(f"parse_version: {report['parse_version'] or '(none)'}")
    comments = report["comments"]
    print(f"comments: {len(comments)}")
    for comment in comments:
        print(
            f"  type={comment['type']} line {comment['line']} column {comment['column']}: "
            f"{comment['text']}"
        )
    spans = report["span_summary"]
    print(
        "nodes: {total_nodes} "
        "(with spans: {nodes_with_span}; without spans: {nodes_without_span})".format(**spans)
    )
    if spans["start"] is not None:
        print(
            "span envelope: L{start[line]}:C{start[column]} to "
            "L{end[line]}:C{end[column]}".format(**spans)
        )
    print("node histogram:")
    for name, count in report["node_histogram"].items():
        print(f"  {name}: {count}")
    if "normalized_source" in report:
        print("normalized source:")
        print(report["normalized_source"], end="" if report["normalized_source"].endswith("\n") else "\n")


def report_error(args: argparse.Namespace, message: str) -> int:
    if args.json:
        print(json.dumps({"error": message}, indent=2))
    else:
        print(f"error: {message}", file=sys.stderr)
    return 1


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        source, _ = read_source(args)
        openqasm3 = load_parser_api()
        report = make_report(source, openqasm3, args)
    except ToolError as exc:
        return report_error(args, str(exc))

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
