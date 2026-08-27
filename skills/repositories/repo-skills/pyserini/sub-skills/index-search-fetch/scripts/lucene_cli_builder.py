#!/usr/bin/env python3
"""Build safe Pyserini Lucene CLI commands without executing Java-backed workflows."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path


DEFAULT_COLLECTION = "JsonCollection"
DEFAULT_GENERATOR = "DefaultLuceneDocumentGenerator"


def quote_command(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def add_common_search_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--index", required=True, help="Path to a Lucene index or Pyserini prebuilt index name.")
    parser.add_argument("--topics", required=True, help="Topics file or prebuilt topic name.")
    parser.add_argument("--output", required=True, help="Run output path.")
    parser.add_argument("--hits", type=int, default=1000, help="Number of hits per query.")
    parser.add_argument("--threads", type=int, default=1, help="Search threads.")
    parser.add_argument("--language", default="en", help="Analyzer language code for sparse search.")
    parser.add_argument("--topics-format", help="Explicit topics format when Pyserini cannot infer it.")
    parser.add_argument("--output-format", help="Explicit output format; default Pyserini format is TREC.")


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return parsed


def build_index(args: argparse.Namespace) -> list[str]:
    command = [
        "python",
        "-m",
        "pyserini.index.lucene",
        "--collection",
        args.collection,
        "--input",
        args.input,
        "--index",
        args.index,
        "--generator",
        args.generator,
        "--threads",
        str(args.threads),
    ]
    if args.language != "en":
        command.extend(["--language", args.language])
    if args.store_positions:
        command.append("--storePositions")
    if args.store_docvectors:
        command.append("--storeDocvectors")
    if args.store_raw:
        command.append("--storeRaw")
    if args.pretokenized:
        command.append("--pretokenized")
    if args.append:
        command.append("--append")
    if args.optimize:
        command.append("--optimize")
    return command


def build_search(args: argparse.Namespace) -> list[str]:
    command = [
        "python",
        "-m",
        "pyserini.search.lucene",
        "--index",
        args.index,
        "--topics",
        args.topics,
        "--output",
        args.output,
        "--hits",
        str(args.hits),
        "--threads",
        str(args.threads),
    ]
    if args.language != "en":
        command.extend(["--language", args.language])
    if args.topics_format:
        command.extend(["--topics-format", args.topics_format])
    if args.output_format:
        command.extend(["--output-format", args.output_format])
    if args.qld:
        command.append("--qld")
    else:
        command.append("--bm25")
        if args.k1 is not None or args.b is not None:
            command.extend(["--k1", str(args.k1), "--b", str(args.b)])
    if args.rm3:
        command.append("--rm3")
    if args.rm3_py:
        command.append("--rm3-py")
    if args.fields:
        command.append("--fields")
        command.extend(args.fields)
    if args.dismax:
        command.append("--dismax")
    if args.pretokenized:
        command.append("--pretokenized")
    return command


def build_fetch_snippet(args: argparse.Namespace) -> str:
    index_literal = repr(args.index)
    docid_literal = repr(args.docid)
    return "\n".join(
        [
            "python - <<'PY'",
            "from pyserini.search.lucene import LuceneSearcher",
            f"searcher = LuceneSearcher({index_literal})",
            f"doc = searcher.doc({docid_literal})",
            "if doc is None:",
            "    raise SystemExit('document not found')",
            "print(doc.raw() or doc.contents() or '')",
            "PY",
        ]
    )


def validate_args(args: argparse.Namespace) -> None:
    if getattr(args, "input", None) and Path(args.input).is_file():
        raise SystemExit("--input must be a directory for pyserini.index.lucene; place JSONL files in a directory")
    if getattr(args, "k1", None) is None and getattr(args, "b", None) is not None:
        raise SystemExit("--k1 and --b must be supplied together")
    if getattr(args, "k1", None) is not None and getattr(args, "b", None) is None:
        raise SystemExit("--k1 and --b must be supplied together")
    if getattr(args, "qld", False) and (getattr(args, "rm3", False) or getattr(args, "rm3_py", False)):
        raise SystemExit("QLD plus RM3 is usually unintended; build separate commands")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print safe Pyserini Lucene CLI commands for indexing, sparse search, or fetch snippets."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="Build a pyserini.index.lucene command.")
    index_parser.add_argument("--input", required=True, help="Collection directory; must not be a single file.")
    index_parser.add_argument("--index", required=True, help="Output Lucene index directory.")
    index_parser.add_argument("--collection", default=DEFAULT_COLLECTION, help="Anserini collection class.")
    index_parser.add_argument("--generator", default=DEFAULT_GENERATOR, help="Anserini document generator.")
    index_parser.add_argument("--threads", type=positive_int, default=1, help="Indexing threads.")
    index_parser.add_argument("--language", default="en", help="Language code, e.g. zh.")
    index_parser.add_argument("--store-positions", action="store_true", help="Add --storePositions.")
    index_parser.add_argument("--store-docvectors", action="store_true", help="Add --storeDocvectors.")
    index_parser.add_argument("--store-raw", action="store_true", help="Add --storeRaw.")
    index_parser.add_argument("--pretokenized", action="store_true", help="Add --pretokenized.")
    index_parser.add_argument("--append", action="store_true", help="Append to an existing index.")
    index_parser.add_argument("--optimize", action="store_true", help="Optimize/merge index segments.")

    search_parser = subparsers.add_parser("search", help="Build a pyserini.search.lucene BM25/QLD/RM3 command.")
    add_common_search_args(search_parser)
    search_parser.add_argument("--k1", type=float, help="BM25 k1 parameter; must be paired with --b.")
    search_parser.add_argument("--b", type=float, help="BM25 b parameter; must be paired with --k1.")
    search_parser.add_argument("--rm3", action="store_true", help="Add RM3 pseudo-relevance feedback.")
    search_parser.add_argument("--rm3-py", action="store_true", help="Use Python RM3 implementation.")
    search_parser.add_argument("--qld", action="store_true", help="Use query likelihood with Dirichlet smoothing instead of BM25.")
    search_parser.add_argument("--fields", nargs="+", help="Field boosts as key=value pairs.")
    search_parser.add_argument("--dismax", action="store_true", help="Use disjunction max for multi-field search.")
    search_parser.add_argument("--pretokenized", action="store_true", help="Accept pre-tokenized topics.")

    fetch_parser = subparsers.add_parser("fetch-snippet", help="Print a Python snippet for fetching a stored document.")
    fetch_parser.add_argument("--index", required=True, help="Path to a Lucene index.")
    fetch_parser.add_argument("--docid", required=True, help="External collection docid string.")

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    validate_args(args)
    if args.command == "index":
        print(quote_command(build_index(args)))
    elif args.command == "search":
        print(quote_command(build_search(args)))
    elif args.command == "fetch-snippet":
        print(build_fetch_snippet(args))
    else:
        raise SystemExit(f"unknown command: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
