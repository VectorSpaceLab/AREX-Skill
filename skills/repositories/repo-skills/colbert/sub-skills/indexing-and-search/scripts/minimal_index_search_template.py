#!/usr/bin/env python3
"""Editable ColBERT indexing and search template.

The script uses public ColBERT APIs and explicit user-provided paths. It is safe
for `--help` without ColBERT installed because imports happen only when a run
mode is selected.
"""

from __future__ import annotations

import argparse
from pathlib import Path


OVERWRITE_CHOICES = ["false", "true", "reuse", "resume", "force_silent_overwrite"]


def existing_file(value: str) -> str:
    path = Path(value).expanduser()
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"file does not exist: {path}")
    return str(path)


def existing_path_or_name(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("value must not be empty")
    return value


def nonempty(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("value must not be empty")
    return value


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("value must be an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def overwrite_value(value: str):
    if value == "false":
        return False
    if value == "true":
        return True
    return value


def add_common_run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", required=True, help="experiment root directory")
    parser.add_argument("--experiment", default="default", help="experiment namespace under --root")
    parser.add_argument("--nranks", type=positive_int, default=1, help="number of ColBERT ranks/processes")


def add_search_tuning_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--ncells", type=positive_int, help="candidate cells; omit for ColBERT's k-based default")
    parser.add_argument("--centroid-score-threshold", type=float, help="candidate pruning threshold")
    parser.add_argument("--ndocs", type=positive_int, help="candidate docs; omit for ColBERT's k-based default")
    parser.add_argument("--load-index-with-mmap", action="store_true", help="CPU-only memory-mapped index loading")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Minimal editable template for ColBERT indexing, single-query search, and batch search.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    index = subparsers.add_parser("index", help="build or reuse a ColBERT index")
    add_common_run_args(index)
    index.add_argument("--checkpoint", required=True, type=existing_path_or_name, help="local checkpoint path or model name")
    index.add_argument("--collection", required=True, type=existing_file, help="collection TSV path")
    index.add_argument("--index-name", required=True, type=nonempty, help="name of the index directory to create")
    index.add_argument("--nbits", type=positive_int, default=2, help="residual compression bits")
    index.add_argument("--doc-maxlen", type=positive_int, default=180, help="passage truncation length")
    index.add_argument("--index-bsize", type=positive_int, help="indexing batch size")
    index.add_argument("--overwrite", choices=OVERWRITE_CHOICES, default="false", help="existing-index policy")

    single = subparsers.add_parser("search", help="run one text query against an existing index")
    add_common_run_args(single)
    add_search_tuning_args(single)
    single.add_argument("--index-name", required=True, type=nonempty, help="index directory basename")
    single.add_argument("--index-root", help="optional directory containing index directories")
    single.add_argument("--checkpoint", type=existing_path_or_name, help="optional checkpoint override")
    single.add_argument("--collection", type=existing_file, help="optional collection TSV for passage lookup")
    single.add_argument("--query", required=True, type=nonempty, help="query text")
    single.add_argument("--k", type=positive_int, default=10, help="number of results")

    batch = subparsers.add_parser("search-all", help="run TSV queries and save a ranking")
    add_common_run_args(batch)
    add_search_tuning_args(batch)
    batch.add_argument("--index-name", required=True, type=nonempty, help="index directory basename")
    batch.add_argument("--index-root", help="optional directory containing index directories")
    batch.add_argument("--checkpoint", type=existing_path_or_name, help="optional checkpoint override")
    batch.add_argument("--collection", type=existing_file, help="optional collection TSV for passage lookup")
    batch.add_argument("--queries", required=True, type=existing_file, help="queries TSV path")
    batch.add_argument("--output", required=True, help="ranking TSV output path; absolute path is easiest to locate")
    batch.add_argument("--k", type=positive_int, default=100, help="number of results per query")

    return parser


def make_config(args):
    from colbert.infra import ColBERTConfig

    kwargs = {"root": args.root}

    for name in [
        "nbits",
        "doc_maxlen",
        "index_bsize",
        "ncells",
        "centroid_score_threshold",
        "ndocs",
        "load_index_with_mmap",
    ]:
        if hasattr(args, name):
            value = getattr(args, name)
            if value is not None:
                kwargs[name] = value

    return ColBERTConfig(**kwargs)


def run_index(args) -> None:
    from colbert import Indexer
    from colbert.infra import Run, RunConfig

    with Run().context(RunConfig(nranks=args.nranks, experiment=args.experiment)):
        config = make_config(args)
        indexer = Indexer(checkpoint=args.checkpoint, config=config)
        index_path = indexer.index(
            name=args.index_name,
            collection=args.collection,
            overwrite=overwrite_value(args.overwrite),
        )
        print(index_path)


def run_search(args) -> None:
    from colbert import Searcher
    from colbert.infra import Run, RunConfig

    with Run().context(RunConfig(nranks=args.nranks, experiment=args.experiment)):
        searcher = Searcher(
            index=args.index_name,
            checkpoint=args.checkpoint,
            collection=args.collection,
            config=make_config(args),
            index_root=args.index_root,
        )
        pids, ranks, scores = searcher.search(args.query, k=args.k)
        for pid, rank, score in zip(pids, ranks, scores):
            passage = searcher.collection[pid] if searcher.collection is not None else ""
            print(f"{rank}\t{pid}\t{score}\t{passage}")


def run_search_all(args) -> None:
    from colbert import Searcher
    from colbert.data import Queries
    from colbert.infra import Run, RunConfig

    with Run().context(RunConfig(nranks=args.nranks, experiment=args.experiment)):
        searcher = Searcher(
            index=args.index_name,
            checkpoint=args.checkpoint,
            collection=args.collection,
            config=make_config(args),
            index_root=args.index_root,
        )
        queries = Queries(args.queries)
        ranking = searcher.search_all(queries, k=args.k)
        output_path = ranking.save(args.output)
        print(output_path)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "index":
        run_index(args)
    elif args.command == "search":
        run_search(args)
    elif args.command == "search-all":
        run_search_all(args)
    else:
        parser.error(f"unknown command: {args.command}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
