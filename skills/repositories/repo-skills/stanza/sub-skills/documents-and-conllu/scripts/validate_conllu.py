#!/usr/bin/env python3
"""Validate CoNLL-U input with Stanza and report document counts."""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, Tuple

from stanza.utils.conll import CoNLL, CoNLLError


def _read_input(path: str) -> Tuple[str, str]:
    if path == "-":
        if sys.stdin.isatty():
            raise ValueError("no input provided on stdin")
        text = sys.stdin.read()
        if not text.strip():
            raise ValueError("empty input")
        return text, "<stdin>"

    try:
        with open(path, encoding="utf-8") as fin:
            text = fin.read()
    except OSError as exc:
        raise OSError(f"cannot read {path}: {exc}") from exc
    if not text.strip():
        raise ValueError("empty input")
    return text, path


def _parse_doc(text: str, source: str, ignore_gapping: bool, keep_line_numbers: bool) -> int:
    try:
        doc = CoNLL.conll2doc(
            input_str=text,
            ignore_gapping=ignore_gapping,
            keep_line_numbers=keep_line_numbers,
        )
    except CoNLLError as exc:
        print(f"{source}: invalid CoNLL-U: {exc}", file=sys.stderr)
        return 1
    except (ValueError, IndexError, AssertionError) as exc:
        print(f"{source}: invalid CoNLL-U: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1

    sentence_count = len(doc.sentences)
    token_count = doc.num_tokens
    word_count = doc.num_words
    empty_node_count = sum(len(sentence.empty_words) for sentence in doc.sentences)
    print(
        f"OK {source}: sentences={sentence_count} tokens={token_count} "
        f"words={word_count} empty_nodes={empty_node_count}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a CoNLL-U file or stdin with Stanza and report counts.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="-",
        help="Path to a CoNLL-U file, or '-' to read from stdin.",
    )
    parser.add_argument(
        "--ignore-gapping",
        action="store_true",
        help="Skip empty-node rows instead of keeping them in the parsed Document (default: keep them).",
    )
    parser.add_argument(
        "--keep-line-numbers",
        action="store_true",
        help="Preserve internal line numbers while parsing.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        text, source = _read_input(args.path)
    except (ValueError, OSError) as exc:
        print(f"{args.path}: {exc}", file=sys.stderr)
        return 2

    return _parse_doc(
        text,
        source,
        ignore_gapping=args.ignore_gapping,
        keep_line_numbers=args.keep_line_numbers,
    )


if __name__ == "__main__":
    raise SystemExit(main())
