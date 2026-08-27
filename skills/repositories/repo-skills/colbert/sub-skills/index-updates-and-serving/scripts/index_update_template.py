#!/usr/bin/env python3
"""Editable template for ColBERT index add/remove/persist workflows.

The script imports ColBERT only when a command is executed, so `--help` remains
safe in lightweight environments. Run against a disposable index copy before
mutating a production index.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def nonempty(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("value must not be empty")
    return value


def existing_file(value: str) -> str:
    path = Path(value).expanduser()
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"file does not exist: {path}")
    return str(path)


def existing_path_or_name(value: str) -> str:
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


def pid_list(value: str) -> list[int]:
    raw = value.strip()
    if not raw:
        return []
    pids = []
    for part in raw.split(","):
        item = part.strip()
        if not item:
            continue
        try:
            pid = int(item)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"invalid pid: {item}") from exc
        if pid < 0:
            raise argparse.ArgumentTypeError(f"pid must be non-negative: {pid}")
        pids.append(pid)
    return pids


def load_passages(path: str | None, inline: list[str] | None) -> list[str]:
    passages: list[str] = []
    if path:
        with open(Path(path).expanduser(), "r", encoding="utf-8") as handle:
            for line in handle:
                text = line.rstrip("\n")
                if text:
                    passages.append(text)
    for text in inline or []:
        if text:
            passages.append(text)
    return passages


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", required=True, help="ColBERT experiment root")
    parser.add_argument("--experiment", default="default", help="ColBERT experiment namespace")
    parser.add_argument("--index-name", required=True, type=nonempty, help="existing index name")
    parser.add_argument("--index-root", help="optional directory containing index directories")
    parser.add_argument("--checkpoint", type=existing_path_or_name, help="checkpoint/model name; required for add")
    parser.add_argument("--collection", type=existing_file, help="optional collection TSV for passage lookup")
    parser.add_argument("--nranks", type=positive_int, default=1, help="RunConfig nranks")
    parser.add_argument("--doc-maxlen", type=positive_int, help="optional config doc_maxlen override")
    parser.add_argument("--nbits", type=positive_int, help="optional config nbits override")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mutate an existing ColBERT index with IndexUpdater.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    apply_update = subparsers.add_parser("apply", help="add/remove passages and optionally persist")
    add_common_args(apply_update)
    apply_update.add_argument("--remove-pids", type=pid_list, default=[], help="comma-separated pids to remove")
    apply_update.add_argument("--add-passages-file", type=existing_file, help="UTF-8 text file with one passage per line")
    apply_update.add_argument("--add-passage", action="append", help="inline passage to append; may be repeated")
    apply_update.add_argument("--persist", action="store_true", help="write changes to the index directory")
    apply_update.add_argument("--query", help="optional query to run after mutation")
    apply_update.add_argument("--k", type=positive_int, default=10, help="top-k for optional validation query")

    reload_check = subparsers.add_parser("reload-check", help="load a fresh Searcher and run a small query")
    add_common_args(reload_check)
    reload_check.add_argument("--query", required=True, type=nonempty, help="query text")
    reload_check.add_argument("--k", type=positive_int, default=10, help="top-k for validation query")

    return parser


def make_config(args):
    from colbert.infra import ColBERTConfig

    kwargs = {"root": args.root}
    if args.doc_maxlen is not None:
        kwargs["doc_maxlen"] = args.doc_maxlen
    if args.nbits is not None:
        kwargs["nbits"] = args.nbits
    return ColBERTConfig(**kwargs)


def make_searcher(args, config):
    from colbert import Searcher

    return Searcher(
        index=args.index_name,
        checkpoint=args.checkpoint,
        collection=args.collection,
        config=config,
        index_root=args.index_root,
    )


def summarize_search(searcher, query: str, k: int) -> list[dict[str, object]]:
    pids, ranks, scores = searcher.search(query, k=k)
    rows = []
    for pid, rank, score in zip(pids, ranks, scores):
        text = ""
        if getattr(searcher, "collection", None) is not None:
            try:
                text = searcher.collection[pid]
            except Exception:
                text = ""
        rows.append({"pid": int(pid), "rank": int(rank), "score": float(score), "text": text})
    return rows


def run_apply(args) -> None:
    from colbert import IndexUpdater
    from colbert.infra import Run, RunConfig

    passages = load_passages(args.add_passages_file, args.add_passage)
    if passages and not args.checkpoint:
        raise SystemExit("--checkpoint is required when adding passages")
    if not args.remove_pids and not passages:
        raise SystemExit("provide --remove-pids, --add-passages-file, or --add-passage")

    with Run().context(RunConfig(nranks=args.nranks, experiment=args.experiment)):
        config = make_config(args)
        searcher = make_searcher(args, config)
        updater = IndexUpdater(config, searcher, checkpoint=args.checkpoint)

        removed = list(args.remove_pids)
        if removed:
            updater.remove(removed)

        added = []
        if passages:
            added = updater.add(passages)

        validation = None
        if args.query:
            validation = summarize_search(searcher, args.query, args.k)

        persisted = False
        if args.persist:
            updater.persist_to_disk()
            persisted = True

        print(json.dumps({"index_path": searcher.index, "removed_pids": removed, "added_pids": added, "persisted": persisted, "validation": validation}, indent=2))


def run_reload_check(args) -> None:
    from colbert.infra import Run, RunConfig

    with Run().context(RunConfig(nranks=args.nranks, experiment=args.experiment)):
        config = make_config(args)
        searcher = make_searcher(args, config)
        print(json.dumps({"index_path": searcher.index, "results": summarize_search(searcher, args.query, args.k)}, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "apply":
        run_apply(args)
    elif args.command == "reload-check":
        run_reload_check(args)
    else:
        parser.error(f"unknown command: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
