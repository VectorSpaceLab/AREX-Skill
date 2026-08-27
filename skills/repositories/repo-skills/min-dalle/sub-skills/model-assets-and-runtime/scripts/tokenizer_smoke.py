#!/usr/bin/env python3
"""
No-network tokenizer smoke for min(DALL·E).

This uses a synthetic vocabulary and merge table. It verifies TextTokenizer
normalization/BPE wrapping without constructing MinDalle, downloading tokenizer
assets, or loading model weights.
"""

from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a synthetic no-network TextTokenizer smoke check.")
    parser.add_argument("--text", default="HELLO 🤖 WALL-E", help="Text to tokenize with the synthetic vocabulary.")
    parser.add_argument("--verbose", action="store_true", help="Print BPE subwords during tokenization.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        from min_dalle.text_tokenizer import TextTokenizer
    except ImportError as exc:
        print(f"cannot import min_dalle.text_tokenizer: {exc}", file=sys.stderr)
        print("Install min-dalle with its emoji dependency before running this smoke.", file=sys.stderr)
        return 2

    word_start = chr(ord(" ") + 256)
    vocab = {
        "<s>": 0,
        "</s>": 1,
        "<unk>": 2,
        word_start + "hello": 3,
        word_start + "wall": 4,
        "e": 5,
        word_start + "robot": 6,
    }
    merges = [
        f"{word_start} h",
        f"{word_start}h e",
        f"{word_start}he l",
        f"{word_start}hel l",
        f"{word_start}hell o",
        f"{word_start} w",
        f"{word_start}w a",
        f"{word_start}wa l",
        f"{word_start}wal l",
        f"{word_start} r",
        f"{word_start}r o",
        f"{word_start}ro b",
        f"{word_start}rob o",
        f"{word_start}robo t",
    ]
    tokenizer = TextTokenizer(vocab, merges)
    tokens = tokenizer.tokenize(args.text, is_verbose=args.verbose)
    print("tokens:", tokens)

    if not tokens or tokens[0] != vocab["<s>"] or tokens[-1] != vocab["</s>"]:
        print("tokenizer did not wrap tokens with <s> and </s>", file=sys.stderr)
        return 1
    if vocab[word_start + "hello"] not in tokens and "hello" in args.text.lower():
        print("expected synthetic 'hello' token missing", file=sys.stderr)
        return 1
    print("tokenizer smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
