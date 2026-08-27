#!/usr/bin/env python3
"""Render a four-choice RWKV MMLU-style prompt and validate label tokens.

This helper is intentionally tiny: it checks whether labels such as " A" are
single tokens in the selected tokenizer and prints the rendered prompt.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def load_tokenizer(tokenizer_spec: str):
    if Path(tokenizer_spec).exists():
        from rwkv.rwkv_tokenizer import TRIE_TOKENIZER

        return TRIE_TOKENIZER(tokenizer_spec)
    from rwkv.utils import PIPELINE

    return PIPELINE(None, tokenizer_spec)


def encode(tokenizer, text: str):
    if hasattr(tokenizer, "encode"):
        return tokenizer.encode(text)
    raise TypeError(f"unsupported tokenizer object: {type(tokenizer)!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tokenizer", required=True, help="Tokenizer file or rwkv pipeline name")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--choice-a", required=True)
    parser.add_argument("--choice-b", required=True)
    parser.add_argument("--choice-c", required=True)
    parser.add_argument("--choice-d", required=True)
    args = parser.parse_args()

    tokenizer = load_tokenizer(args.tokenizer)
    labels = {label: encode(tokenizer, label) for label in [" A", " B", " C", " D"]}
    for label, tokens in labels.items():
        if len(tokens) != 1:
            raise SystemExit(f"label {label!r} is not a single token: {tokens}")

    prompt = (
        f"User: You are a very talented expert in {args.subject}. Answer this question:\n"
        f"{args.question}\n"
        f"A. {args.choice_a}\n"
        f"B. {args.choice_b}\n"
        f"C. {args.choice_c}\n"
        f"D. {args.choice_d}\n\n"
        f"Assistant: The answer is"
    )
    print(prompt)
    print("\n# label tokens")
    for label, tokens in labels.items():
        print(label, tokens)


if __name__ == "__main__":
    main()
