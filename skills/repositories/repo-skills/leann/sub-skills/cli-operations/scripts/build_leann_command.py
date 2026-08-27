#!/usr/bin/env python3
"""Build and validate a LEANN CLI command without executing it."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any, Iterable

SUPPRESS = argparse.SUPPRESS
EMBEDDING_MODES = ("sentence-transformers", "openai", "mlx", "ollama")
LLM_PROVIDERS = (
    "simulated",
    "ollama",
    "hf",
    "openai",
    "anthropic",
    "minimax",
    "novita",
    "atlascloud",
    "atlas-cloud",
    "atlas",
)
PRUNING_STRATEGIES = ("global", "local", "proportional")
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


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def port_number(value: str) -> int:
    parsed = int(value)
    if not 1 <= parsed <= 65535:
        raise argparse.ArgumentTypeError("must be between 1 and 65535")
    return parsed


def ratio(value: str) -> float:
    parsed = float(value)
    if not 0.0 <= parsed <= 1.0:
        raise argparse.ArgumentTypeError("must be between 0 and 1")
    return parsed


def metadata_filter(value: str) -> str:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"not valid JSON: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("must be a JSON object")
    for field, spec in parsed.items():
        if not isinstance(field, str) or not field:
            raise argparse.ArgumentTypeError("field names must be non-empty strings")
        if not isinstance(spec, dict) or not spec:
            raise argparse.ArgumentTypeError(
                f"filter for {field!r} must be a non-empty operator object"
            )
        for operator, expected in spec.items():
            if operator not in FILTER_OPERATORS:
                allowed = ", ".join(sorted(FILTER_OPERATORS))
                raise argparse.ArgumentTypeError(
                    f"unsupported operator {operator!r}; choose one of: {allowed}"
                )
            if operator in {"in", "not_in"} and not isinstance(expected, list):
                raise argparse.ArgumentTypeError(
                    f"operator {operator!r} for {field!r} requires a JSON array"
                )
    return json.dumps(parsed, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def add_value(
    parser: argparse.ArgumentParser,
    flag: str,
    *,
    type: Any = str,
    choices: Iterable[str] | None = None,
    dest: str | None = None,
) -> None:
    parser.add_argument(flag, dest=dest, type=type, choices=choices, default=SUPPRESS)


def add_bool_optional(parser: argparse.ArgumentParser, flag: str, *, dest: str | None = None) -> None:
    parser.add_argument(
        flag,
        dest=dest,
        action=argparse.BooleanOptionalAction,
        default=SUPPRESS,
    )


def add_embedding_options(parser: argparse.ArgumentParser) -> None:
    add_value(parser, "--embedding-model")
    add_value(parser, "--embedding-mode", choices=EMBEDDING_MODES)
    add_value(parser, "--embedding-host")
    add_value(parser, "--embedding-api-base")
    add_value(parser, "--embedding-batch-size", type=positive_int)


def add_indexer_options(parser: argparse.ArgumentParser) -> None:
    add_value(parser, "--index-name", dest="index_name_option")
    add_embedding_options(parser)
    add_value(parser, "--max-count", type=int)
    parser.add_argument("--no-recompute", action="store_true", default=SUPPRESS)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate and print one shell-quoted LEANN command. This helper never executes "
            "LEANN, reads credentials, downloads models, or changes an index."
        )
    )
    parser.add_argument(
        "--check-inputs",
        action="store_true",
        help="require build/export input paths to exist before printing",
    )
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument("-v", "--verbose", action="store_true")
    verbosity.add_argument("-q", "--quiet", action="store_true")
    groups = parser.add_subparsers(dest="command", required=True)

    build = groups.add_parser("build", help="plan leann build")
    build.add_argument("index_name", nargs="?", default=SUPPRESS)
    build.add_argument("--docs", nargs="+", default=SUPPRESS)
    add_value(build, "--backend-name", choices=("hnsw", "diskann", "ivf"))
    add_embedding_options(build)
    add_value(build, "--embedding-prompt-template")
    add_value(build, "--query-prompt-template")
    build.add_argument("--force", "-f", action="store_true", default=SUPPRESS)
    add_value(build, "--graph-degree", type=positive_int)
    add_value(build, "--complexity", type=positive_int)
    add_value(build, "--num-threads", type=positive_int)
    add_bool_optional(build, "--compact")
    add_bool_optional(build, "--recompute")
    add_value(build, "--file-types")
    add_bool_optional(build, "--include-hidden")
    add_value(build, "--doc-chunk-size", type=positive_int)
    add_value(build, "--doc-chunk-overlap", type=non_negative_int)
    add_value(build, "--code-chunk-size", type=positive_int)
    add_value(build, "--code-chunk-overlap", type=non_negative_int)
    build.add_argument("--use-ast-chunking", action="store_true", default=SUPPRESS)
    add_value(build, "--ast-chunk-size", type=positive_int)
    add_value(build, "--ast-chunk-overlap", type=non_negative_int)
    build.add_argument("--ast-fallback-traditional", action="store_true", default=SUPPRESS)
    add_value(build, "--id-scheme", choices=("sequential", "content-hash"))

    watch = groups.add_parser("watch", help="plan leann watch")
    watch.add_argument("index_name")
    add_value(watch, "--interval", type=positive_int)
    watch.add_argument("--once", action="store_true", default=SUPPRESS)
    watch.add_argument("--dry-run", action="store_true", default=SUPPRESS)

    migrate = groups.add_parser("migrate-ids", help="plan leann migrate-ids")
    migrate.add_argument("index_name")
    migrate.add_argument("--dry-run", action="store_true", default=SUPPRESS)
    migrate.add_argument("-y", "--yes", action="store_true", default=SUPPRESS)

    rebuild = groups.add_parser("rebuild", help="plan leann rebuild")
    rebuild.add_argument("index_name")
    rebuild.add_argument("-f", "--force", action="store_true", default=SUPPRESS)

    search = groups.add_parser("search", help="plan leann search")
    search.add_argument("index_name")
    search.add_argument("query")
    add_value(search, "--top-k", type=positive_int)
    add_value(search, "--complexity", type=positive_int)
    add_value(search, "--beam-width", type=positive_int)
    add_value(search, "--prune-ratio", type=ratio)
    add_bool_optional(search, "--recompute")
    add_value(search, "--pruning-strategy", choices=PRUNING_STRATEGIES)
    search.add_argument("--json", action="store_true", default=SUPPRESS)
    search.add_argument("--non-interactive", action="store_true", default=SUPPRESS)
    search.add_argument("--show-metadata", action="store_true", default=SUPPRESS)
    add_value(search, "--embedding-prompt-template")
    add_bool_optional(search, "--daemon")
    add_value(search, "--daemon-ttl", type=non_negative_int)
    add_bool_optional(search, "--warmup")
    add_value(search, "--metadata-filters", type=metadata_filter)

    warmup = groups.add_parser("warmup", help="plan leann warmup")
    warmup.add_argument("index_name")
    add_bool_optional(warmup, "--daemon")
    add_value(warmup, "--daemon-ttl", type=non_negative_int)
    add_bool_optional(warmup, "--warmup")

    daemon = groups.add_parser("daemon", help="plan leann daemon")
    daemon_actions = daemon.add_subparsers(dest="daemon_command", required=True)
    daemon_start = daemon_actions.add_parser("start")
    daemon_start.add_argument("index_name")
    add_value(daemon_start, "--daemon-ttl", type=non_negative_int)
    add_bool_optional(daemon_start, "--warmup")
    daemon_stop = daemon_actions.add_parser("stop")
    daemon_stop.add_argument("index_name", nargs="?", default=SUPPRESS)
    daemon_stop.add_argument("--all", action="store_true", default=SUPPRESS)
    daemon_status = daemon_actions.add_parser("status")
    daemon_status.add_argument("index_name", nargs="?", default=SUPPRESS)

    ask = groups.add_parser("ask", help="plan leann ask")
    ask.add_argument("index_name")
    ask.add_argument("query", nargs="?", default=SUPPRESS)
    add_value(ask, "--llm", choices=LLM_PROVIDERS)
    add_value(ask, "--model")
    add_value(ask, "--host")
    ask.add_argument("--interactive", "-i", action="store_true", default=SUPPRESS)
    add_value(ask, "--top-k", type=positive_int)
    add_value(ask, "--complexity", type=positive_int)
    add_value(ask, "--beam-width", type=positive_int)
    add_value(ask, "--prune-ratio", type=ratio)
    add_bool_optional(ask, "--recompute")
    add_value(ask, "--pruning-strategy", choices=PRUNING_STRATEGIES)
    add_value(ask, "--thinking-budget", choices=("low", "medium", "high"))
    add_value(ask, "--api-base")
    add_value(ask, "--metadata-filters", type=metadata_filter)

    react = groups.add_parser("react", help="plan leann react")
    react.add_argument("index_name")
    react.add_argument("query")
    add_value(react, "--llm", choices=LLM_PROVIDERS)
    add_value(react, "--model")
    add_value(react, "--host")
    add_value(react, "--top-k", type=positive_int)
    add_value(react, "--max-iterations", type=positive_int)
    add_value(react, "--api-base")

    browser = groups.add_parser("index-browser", help="plan leann index-browser")
    browser.add_argument("browser", nargs="?", choices=("chrome", "brave"), default=SUPPRESS)
    add_indexer_options(browser)
    for command in ("index-email", "index-calendar", "index-imessage"):
        indexer = groups.add_parser(command, help=f"plan leann {command}")
        add_indexer_options(indexer)
    wechat = groups.add_parser("index-wechat", help="plan leann index-wechat")
    add_indexer_options(wechat)
    wechat.add_argument("--export-dir", required=True)
    chatgpt = groups.add_parser("index-chatgpt", help="plan leann index-chatgpt")
    add_indexer_options(chatgpt)
    chatgpt.add_argument("--export-path", required=True)
    claude = groups.add_parser("index-claude", help="plan leann index-claude")
    add_indexer_options(claude)
    claude.add_argument("--export-path", required=True)

    list_parser = groups.add_parser("list", help="plan leann list")
    add_value(list_parser, "--max-depth", type=non_negative_int)
    remove = groups.add_parser("remove", help="plan leann remove")
    remove.add_argument("index_name")
    remove.add_argument("--force", "-f", action="store_true", default=SUPPRESS)
    serve = groups.add_parser("serve", help="plan leann serve")
    add_value(serve, "--host")
    add_value(serve, "--port", type=port_number)

    return parser


VALUE_OPTIONS = {
    "backend_name": "--backend-name",
    "embedding_model": "--embedding-model",
    "embedding_mode": "--embedding-mode",
    "embedding_host": "--embedding-host",
    "embedding_api_base": "--embedding-api-base",
    "embedding_batch_size": "--embedding-batch-size",
    "embedding_prompt_template": "--embedding-prompt-template",
    "query_prompt_template": "--query-prompt-template",
    "graph_degree": "--graph-degree",
    "complexity": "--complexity",
    "num_threads": "--num-threads",
    "file_types": "--file-types",
    "doc_chunk_size": "--doc-chunk-size",
    "doc_chunk_overlap": "--doc-chunk-overlap",
    "code_chunk_size": "--code-chunk-size",
    "code_chunk_overlap": "--code-chunk-overlap",
    "ast_chunk_size": "--ast-chunk-size",
    "ast_chunk_overlap": "--ast-chunk-overlap",
    "id_scheme": "--id-scheme",
    "interval": "--interval",
    "top_k": "--top-k",
    "beam_width": "--beam-width",
    "prune_ratio": "--prune-ratio",
    "pruning_strategy": "--pruning-strategy",
    "daemon_ttl": "--daemon-ttl",
    "metadata_filters": "--metadata-filters",
    "llm": "--llm",
    "model": "--model",
    "host": "--host",
    "thinking_budget": "--thinking-budget",
    "api_base": "--api-base",
    "max_iterations": "--max-iterations",
    "index_name_option": "--index-name",
    "max_count": "--max-count",
    "export_dir": "--export-dir",
    "export_path": "--export-path",
    "max_depth": "--max-depth",
    "port": "--port",
}
BOOLEAN_OPTIONALS = {
    "compact": "--compact",
    "recompute": "--recompute",
    "include_hidden": "--include-hidden",
    "daemon": "--daemon",
    "warmup": "--warmup",
}
TRUE_FLAGS = {
    "force": "--force",
    "use_ast_chunking": "--use-ast-chunking",
    "ast_fallback_traditional": "--ast-fallback-traditional",
    "dry_run": "--dry-run",
    "yes": "--yes",
    "once": "--once",
    "json": "--json",
    "non_interactive": "--non-interactive",
    "show_metadata": "--show-metadata",
    "interactive": "--interactive",
    "all": "--all",
    "no_recompute": "--no-recompute",
}


def check_inputs(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if not args.check_inputs:
        return
    paths: list[tuple[str, str]] = []
    if args.command == "build":
        paths.extend(("document input", value) for value in getattr(args, "docs", []))
    elif args.command == "index-wechat":
        paths.append(("export directory", args.export_dir))
    elif args.command in {"index-chatgpt", "index-claude"}:
        paths.append(("export path", args.export_path))
    missing = [(label, value) for label, value in paths if not Path(value).expanduser().exists()]
    if missing:
        details = "; ".join(f"{label} does not exist: {value}" for label, value in missing)
        parser.error(details)
    if args.command == "index-wechat" and not Path(args.export_dir).expanduser().is_dir():
        parser.error(f"export directory is not a directory: {args.export_dir}")


def render_command(args: argparse.Namespace) -> list[str]:
    tokens = ["leann"]
    if args.verbose:
        tokens.append("--verbose")
    elif args.quiet:
        tokens.append("--quiet")
    tokens.append(args.command)
    if args.command == "daemon":
        tokens.append(args.daemon_command)

    if hasattr(args, "index_name"):
        tokens.append(str(args.index_name))
    if args.command == "search":
        tokens.append(args.query)
    elif args.command == "ask" and hasattr(args, "query"):
        tokens.append(args.query)
    elif args.command == "react":
        tokens.append(args.query)
    elif args.command == "index-browser" and hasattr(args, "browser"):
        tokens.append(args.browser)

    if hasattr(args, "docs"):
        tokens.append("--docs")
        tokens.extend(args.docs)

    values = vars(args)
    for dest, flag in VALUE_OPTIONS.items():
        if dest not in values:
            continue
        tokens.extend([flag, str(values[dest])])

    for dest, flag in BOOLEAN_OPTIONALS.items():
        if dest in values:
            tokens.append(flag if values[dest] else f"--no-{flag[2:]}")
    for dest, flag in TRUE_FLAGS.items():
        if values.get(dest):
            tokens.append(flag)
    return tokens


def main(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)
    check_inputs(args, parser)
    print(shlex.join(render_command(args)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
