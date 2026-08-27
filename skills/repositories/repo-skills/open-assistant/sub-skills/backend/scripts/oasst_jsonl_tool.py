#!/usr/bin/env python3
"""Safe Open-Assistant JSONL utility.

Subcommands inspect, tree-to-messages, filter-messages, filter-trees, and
split-messages operate on `.jsonl` and `.jsonl.gz` files without database or
network access.
"""

from __future__ import annotations

import argparse
import gzip
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Iterator, TextIO


def smart_open(path: Path, mode: str) -> TextIO:
    if path.suffix == ".gz":
        return gzip.open(path, mode + "t", encoding="utf-8")
    return path.open(mode, encoding="utf-8")


def read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with smart_open(path, "r") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            if not isinstance(obj, dict):
                raise SystemExit(f"{path}:{line_no}: expected JSON object, got {type(obj).__name__}")
            yield obj


def ensure_output(path: Path, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise SystemExit(f"refusing to overwrite existing output: {path} (pass --overwrite)")
    path.parent.mkdir(parents=True, exist_ok=True)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]], *, exclude_nulls: bool, overwrite: bool) -> int:
    ensure_output(path, overwrite)
    count = 0
    with smart_open(path, "w") as fh:
        for row in rows:
            if exclude_nulls:
                row = drop_nulls(row)
            json.dump(row, fh, ensure_ascii=False)
            fh.write("\n")
            count += 1
    return count


def drop_nulls(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: drop_nulls(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [drop_nulls(v) for v in value]
    return value


def classify(obj: dict[str, Any]) -> str:
    if "message_id" in obj:
        return "message"
    if "message_tree_id" in obj:
        return "tree"
    if "thread_id" in obj:
        return "thread"
    return "unknown"


def walk_messages(node: dict[str, Any] | None) -> Iterator[dict[str, Any]]:
    if not isinstance(node, dict):
        return
    yield node
    for child in node.get("replies") or []:
        if isinstance(child, dict):
            yield from walk_messages(child)


def flatten_tree(tree: dict[str, Any]) -> Iterator[dict[str, Any]]:
    prompt = tree.get("prompt")
    if not isinstance(prompt, dict):
        return
    tree_id = tree.get("message_tree_id")
    tree_state = tree.get("tree_state")
    for msg in walk_messages(prompt):
        out = dict(msg)
        out.pop("replies", None)
        out.setdefault("message_tree_id", tree_id)
        out.setdefault("tree_state", tree_state)
        yield out


def comma_set(value: str | None) -> set[str] | None:
    if value is None:
        return None
    return {x.strip() for x in value.split(",") if x.strip()}


def is_spam(msg: dict[str, Any]) -> bool:
    return msg.get("review_result") is False


def include_by_common_filters(msg: dict[str, Any], args: argparse.Namespace) -> bool:
    langs = comma_set(getattr(args, "lang", None))
    states = comma_set(getattr(args, "state", None))
    roles = comma_set(getattr(args, "role", None))
    if langs is not None and msg.get("lang") not in langs:
        return False
    if states is not None and msg.get("tree_state") not in states:
        return False
    if roles is not None and msg.get("role") not in roles:
        return False
    if getattr(args, "prompts_only", False) and msg.get("parent_id"):
        return False
    text_contains = getattr(args, "text_contains", None)
    if text_contains and text_contains.lower() not in str(msg.get("text", "")).lower():
        return False

    deleted = msg.get("deleted") is True
    synthetic = msg.get("synthetic") is True
    if getattr(args, "deleted_only", False):
        if not deleted:
            return False
    elif not getattr(args, "include_deleted", False) and deleted:
        return False

    if getattr(args, "spam_only", False):
        if not is_spam(msg):
            return False
    elif not getattr(args, "include_spam", False) and is_spam(msg):
        return False

    if getattr(args, "synthetic_only", False):
        if not synthetic:
            return False
    elif not getattr(args, "include_synthetic", False) and synthetic:
        return False

    return True


def cmd_inspect(args: argparse.Namespace) -> int:
    counts = Counter()
    langs = Counter()
    roles = Counter()
    states = Counter()
    missing = Counter()
    sample_ids: list[str] = []
    for obj in read_jsonl(args.input):
        typ = classify(obj)
        counts[typ] += 1
        if typ == "tree":
            states[str(obj.get("tree_state"))] += 1
            msgs = list(walk_messages(obj.get("prompt")))
        elif typ == "message":
            msgs = [obj]
        else:
            msgs = []
        for msg in msgs:
            for key in ("message_id", "text", "role"):
                if key not in msg:
                    missing[key] += 1
            if msg.get("message_id") and len(sample_ids) < args.sample:
                sample_ids.append(str(msg["message_id"]))
            if msg.get("lang"):
                langs[str(msg["lang"])] += 1
            if msg.get("role"):
                roles[str(msg["role"])] += 1
            if msg.get("tree_state"):
                states[str(msg["tree_state"])] += 1
            if msg.get("deleted") is True:
                counts["deleted_messages"] += 1
            if is_spam(msg):
                counts["failed_review_messages"] += 1
            if msg.get("synthetic") is True:
                counts["synthetic_messages"] += 1
    print(json.dumps({
        "objects": counts,
        "languages": langs,
        "roles": roles,
        "tree_states": states,
        "missing_message_fields": missing,
        "sample_message_ids": sample_ids,
    }, indent=2, default=dict))
    return 0


def cmd_tree_to_messages(args: argparse.Namespace) -> int:
    def rows() -> Iterator[dict[str, Any]]:
        for obj in read_jsonl(args.input):
            if classify(obj) != "tree":
                raise SystemExit("tree-to-messages expects every input line to be a tree object")
            yield from flatten_tree(obj)
    count = write_jsonl(args.output, rows(), exclude_nulls=args.exclude_nulls, overwrite=args.overwrite)
    print(f"wrote {count} messages to {args.output}")
    return 0


def iter_messages_for_filter(args: argparse.Namespace) -> Iterator[dict[str, Any]]:
    for obj in read_jsonl(args.input):
        typ = classify(obj)
        if typ == "message":
            yield obj
        elif typ == "tree" and args.flatten_trees:
            yield from flatten_tree(obj)
        elif typ == "tree":
            raise SystemExit("filter-messages saw tree input; pass --flatten-trees or use tree-to-messages first")
        else:
            raise SystemExit(f"filter-messages does not support {typ} objects")


def cmd_filter_messages(args: argparse.Namespace) -> int:
    rows = (msg for msg in iter_messages_for_filter(args) if include_by_common_filters(msg, args))
    count = write_jsonl(args.output, rows, exclude_nulls=args.exclude_nulls, overwrite=args.overwrite)
    print(f"wrote {count} messages to {args.output}")
    return 0


def cmd_filter_trees(args: argparse.Namespace) -> int:
    wanted_states = None if args.states == "all" else comma_set(args.states)
    langs = comma_set(args.lang)

    def keep_tree(tree: dict[str, Any]) -> bool:
        if wanted_states is not None and tree.get("tree_state") not in wanted_states:
            return False
        msgs = list(walk_messages(tree.get("prompt")))
        if langs is not None and not any(msg.get("lang") in langs for msg in msgs):
            return False
        if not args.allow_synthetic and any(msg.get("synthetic") is True for msg in msgs):
            return False
        if args.min_messages is not None and len(msgs) < args.min_messages:
            return False
        if args.max_messages is not None and len(msgs) > args.max_messages:
            return False
        return True

    def rows() -> Iterator[dict[str, Any]]:
        for obj in read_jsonl(args.input):
            if classify(obj) != "tree":
                raise SystemExit("filter-trees expects every input line to be a tree object")
            if keep_tree(obj):
                yield obj
    count = write_jsonl(args.output, rows(), exclude_nulls=args.exclude_nulls, overwrite=args.overwrite)
    print(f"wrote {count} trees to {args.output}")
    return 0


def cmd_split_messages(args: argparse.Namespace) -> int:
    messages = list(read_jsonl(args.input))
    if any(classify(m) != "message" for m in messages):
        raise SystemExit("split-messages expects flat message objects")
    by_tree: dict[str, list[dict[str, Any]]] = {}
    for idx, msg in enumerate(messages):
        tree_id = msg.get("message_tree_id")
        if not tree_id:
            if not args.fallback_id:
                raise SystemExit("message lacks message_tree_id; pass --fallback-id to split by message_id/index")
            tree_id = msg.get("message_id") or f"row-{idx}"
        by_tree.setdefault(str(tree_id), []).append(msg)
    keys = list(by_tree)
    rnd = random.Random(args.seed)
    rnd.shuffle(keys)
    val_n = len(keys) * args.val_percent // 100
    val_keys = set(keys[:val_n])
    train_rows = [m for k in keys if k not in val_keys for m in by_tree[k]]
    val_rows = [m for k in keys if k in val_keys for m in by_tree[k]]
    train_count = write_jsonl(args.train_output, train_rows, exclude_nulls=args.exclude_nulls, overwrite=args.overwrite)
    val_count = write_jsonl(args.val_output, val_rows, exclude_nulls=args.exclude_nulls, overwrite=args.overwrite)
    print(f"wrote train={train_count} val={val_count} using trees={len(keys)} val_percent={args.val_percent}")
    return 0


def add_common_message_filters(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--lang", help="Comma-separated BCP47 language tags.")
    parser.add_argument("--state", help="Comma-separated tree_state values.")
    parser.add_argument("--role", help="Comma-separated roles, e.g. prompter,assistant.")
    parser.add_argument("--prompts-only", action="store_true")
    parser.add_argument("--include-deleted", action="store_true")
    parser.add_argument("--deleted-only", action="store_true")
    parser.add_argument("--include-spam", action="store_true")
    parser.add_argument("--spam-only", action="store_true")
    parser.add_argument("--include-synthetic", action="store_true")
    parser.add_argument("--synthetic-only", action="store_true")
    parser.add_argument("--text-contains")


def add_output_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--exclude-nulls", action="store_true")
    parser.add_argument("--overwrite", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safe Open-Assistant JSONL utility.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("inspect")
    p.add_argument("input", type=Path)
    p.add_argument("--sample", type=int, default=5)
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("tree-to-messages")
    p.add_argument("input", type=Path)
    p.add_argument("output", type=Path)
    add_output_flags(p)
    p.set_defaults(func=cmd_tree_to_messages)

    p = sub.add_parser("filter-messages")
    p.add_argument("input", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--flatten-trees", action="store_true")
    add_common_message_filters(p)
    add_output_flags(p)
    p.set_defaults(func=cmd_filter_messages)

    p = sub.add_parser("filter-trees")
    p.add_argument("input", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--states", default="ready_for_export")
    p.add_argument("--lang")
    p.add_argument("--allow-synthetic", action="store_true")
    p.add_argument("--min-messages", type=int)
    p.add_argument("--max-messages", type=int)
    add_output_flags(p)
    p.set_defaults(func=cmd_filter_trees)

    p = sub.add_parser("split-messages")
    p.add_argument("input", type=Path)
    p.add_argument("--train-output", required=True, type=Path)
    p.add_argument("--val-output", required=True, type=Path)
    p.add_argument("--val-percent", type=int, default=5)
    p.add_argument("--seed", type=int, default=13)
    p.add_argument("--fallback-id", action="store_true")
    add_output_flags(p)
    p.set_defaults(func=cmd_split_messages)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
