#!/usr/bin/env python3
"""Print a validated LEANN RAG command without executing or reading source data."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

SUPPORTED_AST_EXTENSIONS = (".py", ".java", ".cs", ".ts", ".tsx", ".js", ".jsx")
FILTER_OPERATORS = {
    "==",
    "!=",
    "<",
    "<=",
    ">",
    ">=",
    "in",
    "not_in",
    "contains",
    "starts_with",
    "ends_with",
    "is_true",
    "is_false",
}
INDEX_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
MACOS_PRIVATE_SOURCES = {"browser", "email", "calendar", "imessage"}


class PlanningError(ValueError):
    """Raised when a command would be ambiguous or unsafe to print."""


@dataclass(frozen=True)
class Plan:
    family: str
    command: list[str]
    private_data: bool
    executes: bool = False
    reads_source_data: bool = False
    notes: tuple[str, ...] = ()


def _positive(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def _non_negative(value: str) -> int:
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return number


def _validate_index_name(value: str) -> str:
    if not INDEX_NAME_RE.fullmatch(value):
        raise PlanningError(
            "index name must start with an alphanumeric character and contain only "
            "letters, digits, '.', '_', or '-' (maximum 128 characters)"
        )
    return value


def _validate_chunk_pair(size: int, overlap: int, label: str) -> None:
    if size <= 0:
        raise PlanningError(f"{label} chunk size must be positive")
    if overlap < 0 or overlap >= size:
        raise PlanningError(f"{label} overlap must satisfy 0 <= overlap < size")


def _normalize_extensions(values: Sequence[str] | None) -> list[str] | None:
    if values is None:
        return None
    normalized: list[str] = []
    for raw in values:
        value = raw.strip().lower()
        if not value:
            raise PlanningError("file extensions must not be empty")
        if "," in value or "/" in value or "\\" in value or any(ch.isspace() for ch in value):
            raise PlanningError(f"invalid file extension: {raw!r}")
        if not value.startswith("."):
            value = f".{value}"
        if not re.fullmatch(r"\.[a-z0-9][a-z0-9+_-]*", value):
            raise PlanningError(f"invalid file extension: {raw!r}")
        if value not in normalized:
            normalized.append(value)
    if not normalized:
        raise PlanningError("at least one file extension is required")
    return normalized


def _check_source_path(raw: str, expected: str = "either") -> None:
    """Stat a path without enumerating or opening its contents."""
    path = Path(raw).expanduser()
    if not path.exists():
        raise PlanningError(f"source path does not exist: {raw}")
    if expected == "directory" and not path.is_dir():
        raise PlanningError(f"source path must be a directory: {raw}")
    if expected == "file" and not path.is_file():
        raise PlanningError(f"source path must be a file: {raw}")
    if expected == "either" and not (path.is_file() or path.is_dir()):
        raise PlanningError(f"source path must be a regular file or directory: {raw}")


def _validate_filters(raw: str) -> str:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PlanningError(f"metadata filters are not valid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise PlanningError("metadata filters must be a JSON object")
    for field, spec in value.items():
        if not isinstance(field, str) or not field:
            raise PlanningError("metadata filter field names must be non-empty strings")
        if not isinstance(spec, dict) or not spec:
            raise PlanningError(f"metadata filter for {field!r} must be a non-empty object")
        for operator, expected in spec.items():
            if operator not in FILTER_OPERATORS:
                raise PlanningError(f"unsupported metadata filter operator: {operator}")
            if operator in {"in", "not_in"} and not isinstance(expected, list):
                raise PlanningError(f"metadata filter operator {operator!r} requires a JSON list")
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _add_build_arguments(parser: argparse.ArgumentParser, *, code_defaults: bool) -> None:
    parser.add_argument("sources", nargs="+", help="Existing document/code files or directories")
    parser.add_argument("--index", required=True, help="Safe index name")
    parser.add_argument(
        "--file-types",
        nargs="+",
        default=list(SUPPORTED_AST_EXTENSIONS) if code_defaults else None,
        metavar="EXT",
        help="Extension allowlist; code mode defaults to supported AST extensions",
    )
    parser.add_argument("--doc-chunk-size", type=_positive, default=256)
    parser.add_argument("--doc-chunk-overlap", type=_non_negative, default=128)
    parser.add_argument("--code-chunk-size", type=_positive, default=512)
    parser.add_argument("--code-chunk-overlap", type=_non_negative, default=50)
    parser.add_argument("--ast-chunk-size", type=_positive, default=300)
    parser.add_argument("--ast-chunk-overlap", type=_non_negative, default=64)
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Explicitly include hidden paths; omitted by default",
    )


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate inputs and print a public LEANN command. The planner never "
            "executes LEANN, opens source files, starts services, reads credentials, "
            "installs packages, or downloads models."
        )
    )
    parser.add_argument(
        "--format",
        choices=("shell", "json"),
        default="shell",
        help="Output shell command (default) or a machine-readable plan",
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    document = subparsers.add_parser("document", help="Plan a local document build")
    _add_build_arguments(document, code_defaults=False)
    document.add_argument(
        "--use-ast-chunking",
        action="store_true",
        help="Use AST chunking for recognized code within a mixed document corpus",
    )

    code = subparsers.add_parser("code", help="Plan a code or mixed code/prose build")
    _add_build_arguments(code, code_defaults=True)

    personal = subparsers.add_parser(
        "personal", help="Plan a bounded private-source public CLI command"
    )
    personal.add_argument(
        "source_kind", choices=("browser", "email", "calendar", "imessage", "wechat")
    )
    personal.add_argument("--index", required=True, help="Safe, non-sensitive index name")
    personal.add_argument(
        "--source",
        help="Existing WeChat export directory; unsupported for default Apple/browser stores",
    )
    personal.add_argument("--browser", choices=("chrome", "brave"), default="chrome")
    personal.add_argument("--max-count", type=_positive, default=100)
    personal.add_argument(
        "--ack-private-data",
        action="store_true",
        help="Acknowledge that the printed command would access private data if later run",
    )

    search = subparsers.add_parser("search", help="Plan a retrieval-only search command")
    search.add_argument("index", help="Existing index name")
    search.add_argument("query", help="Non-empty semantic query")
    search.add_argument("--top-k", type=_positive, default=5)
    search.add_argument("--metadata-filters", help="Metadata filter JSON object")
    search.add_argument("--show-metadata", action="store_true")

    return parser


def _build_file_plan(args: argparse.Namespace) -> Plan:
    index = _validate_index_name(args.index)
    _validate_chunk_pair(args.doc_chunk_size, args.doc_chunk_overlap, "document")
    _validate_chunk_pair(args.code_chunk_size, args.code_chunk_overlap, "code")
    _validate_chunk_pair(args.ast_chunk_size, args.ast_chunk_overlap, "AST")
    for source in args.sources:
        _check_source_path(source)
    extensions = _normalize_extensions(args.file_types)
    use_ast = args.mode == "code" or bool(getattr(args, "use_ast_chunking", False))

    command = ["leann", "build", index, "--docs", *args.sources]
    if extensions:
        command.extend(["--file-types", ",".join(extensions)])
    command.extend(
        [
            "--doc-chunk-size",
            str(args.doc_chunk_size),
            "--doc-chunk-overlap",
            str(args.doc_chunk_overlap),
            "--code-chunk-size",
            str(args.code_chunk_size),
            "--code-chunk-overlap",
            str(args.code_chunk_overlap),
        ]
    )
    if use_ast:
        command.extend(
            [
                "--use-ast-chunking",
                "--ast-chunk-size",
                str(args.ast_chunk_size),
                "--ast-chunk-overlap",
                str(args.ast_chunk_overlap),
            ]
        )
    if args.include_hidden:
        command.append("--include-hidden")

    notes = ["No force rebuild flag is emitted.", "AST failures retain traditional fallback."]
    if args.include_hidden:
        notes.append("Hidden input inclusion was explicitly requested; review before execution.")
    return Plan(family=args.mode, command=command, private_data=False, notes=tuple(notes))


def _build_personal_plan(args: argparse.Namespace, platform_name: str | None = None) -> Plan:
    platform_name = sys.platform if platform_name is None else platform_name
    kind = args.source_kind

    # Deliberately reject platform before any private-path stat.
    if kind in MACOS_PRIVATE_SOURCES and platform_name != "darwin":
        raise PlanningError(f"{kind} private-source indexing is unsupported on {platform_name}")
    if not args.ack_private_data:
        raise PlanningError("--ack-private-data is required for personal-source planning")

    index = _validate_index_name(args.index)
    if kind == "wechat":
        if not args.source:
            raise PlanningError("--source is required for an existing WeChat export directory")
        _check_source_path(args.source, expected="directory")
        command = [
            "leann",
            "index-wechat",
            "--export-dir",
            args.source,
            "--index-name",
            index,
            "--max-count",
            str(args.max_count),
        ]
    else:
        if args.source:
            raise PlanningError(
                f"--source is not supported by the public {kind} command; it uses the default store"
            )
        command = ["leann", f"index-{kind}"]
        if kind == "browser":
            command.append(args.browser)
        command.extend(["--index-name", index, "--max-count", str(args.max_count)])

    return Plan(
        family=f"personal:{kind}",
        command=command,
        private_data=True,
        notes=(
            "This command is printed only and would access private data if later executed.",
            "No export, credential, service, force rebuild, or model option is emitted.",
        ),
    )


def _build_search_plan(args: argparse.Namespace) -> Plan:
    index = _validate_index_name(args.index)
    query = args.query.strip()
    if not query:
        raise PlanningError("search query must not be empty")
    command = ["leann", "search", index, query, "--top-k", str(args.top_k)]
    if args.metadata_filters:
        command.extend(["--metadata-filters", _validate_filters(args.metadata_filters)])
    if args.show_metadata:
        command.append("--show-metadata")
    return Plan(
        family="search",
        command=command,
        private_data=False,
        notes=("Retrieval only; no chat provider or credential option is emitted.",),
    )


def build_plan(args: argparse.Namespace) -> Plan:
    if args.mode in {"document", "code"}:
        return _build_file_plan(args)
    if args.mode == "personal":
        return _build_personal_plan(args)
    if args.mode == "search":
        return _build_search_plan(args)
    raise PlanningError(f"unsupported planner mode: {args.mode}")


def emit_plan(plan: Plan, output_format: str) -> None:
    shell_command = shlex.join(plan.command)
    if output_format == "shell":
        print(shell_command)
        return
    payload: dict[str, Any] = asdict(plan)
    payload["shell_command"] = shell_command
    print(json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False))


def main(argv: Sequence[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        plan = build_plan(args)
    except PlanningError as exc:
        parser.error(str(exc))
    emit_plan(plan, args.format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
