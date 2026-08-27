#!/usr/bin/env python3
"""
Tiny, deterministic BPE learning and encoding demo for the
attention-is-all-you-need-pytorch data-preparation skill.

This is a safe adaptation of the repository's learn_bpe.py/apply_bpe.py logic:
it learns merge pairs from local text, applies the same version-0.2 end-of-word
convention, appends a separator to non-final subword units, and never downloads
WMT data or imports repository source.

Examples:
  python bpe_tiny_demo.py
  python bpe_tiny_demo.py --symbols 8 --min-frequency 2 --json
  python bpe_tiny_demo.py --corpus tiny.de tiny.en --encode "low lower lowest" --write-dir /tmp/tiny-bpe-demo
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

DEFAULT_CORPUS = [
    "low lower lowest",
    "newer lower wider",
    "low lowest newer",
    "wider low lower",
]
DEFAULT_ENCODE = [
    "low lower lowest",
    "newer wider unknown",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Learn and apply tiny local BPE codes without downloads."
    )
    parser.add_argument(
        "--corpus",
        nargs="*",
        help="UTF-8 text files used for learning. Defaults to a built-in tiny corpus.",
    )
    parser.add_argument(
        "--encode",
        nargs="*",
        help="Sentences to encode after learning. Defaults to built-in examples.",
    )
    parser.add_argument(
        "--symbols",
        "-s",
        type=int,
        default=12,
        help="Maximum number of merge operations to learn (default: 12).",
    )
    parser.add_argument(
        "--min-frequency",
        type=int,
        default=2,
        help="Stop when no symbol pair has at least this frequency (default: 2).",
    )
    parser.add_argument(
        "--separator",
        default="@@",
        help="Separator appended to non-final subword units (default: @@).",
    )
    parser.add_argument(
        "--write-dir",
        help="Optional scratch directory where codes.txt and encoded.txt are written.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a human-readable report.",
    )
    return parser.parse_args()


def read_corpus(paths):
    if not paths:
        return list(DEFAULT_CORPUS), "built-in"
    lines = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                text = line.strip()
                if text:
                    lines.append(text)
    return lines, "files"


def word_to_symbols(word):
    if not word:
        return tuple()
    if len(word) == 1:
        return (word + "</w>",)
    return tuple(word[:-1]) + (word[-1] + "</w>",)


def collect_vocabulary(lines):
    counts = Counter()
    for line in lines:
        for word in line.strip().split():
            if word:
                counts[word_to_symbols(word)] += 1
    return dict(counts)


def pair_statistics(vocab):
    stats = defaultdict(int)
    for symbols, freq in vocab.items():
        for pair in zip(symbols, symbols[1:]):
            stats[pair] += freq
    return stats


def merge_pair(pair, vocab):
    first, second = pair
    pattern = re.compile(r"(?<!\S)" + re.escape(first + " " + second) + r"(?!\S)")
    replacement = first + second
    merged = {}
    for symbols, freq in vocab.items():
        new_symbols = tuple(pattern.sub(replacement, " ".join(symbols)).split(" "))
        merged[new_symbols] = freq
    return merged


def learn_bpe(lines, symbols, min_frequency):
    if symbols < 0:
        raise ValueError("--symbols must be non-negative")
    if min_frequency < 1:
        raise ValueError("--min-frequency must be at least 1")
    vocab = collect_vocabulary(lines)
    codes = []
    for _ in range(symbols):
        stats = pair_statistics(vocab)
        if not stats:
            break
        best = max(stats, key=lambda pair: (stats[pair], pair))
        if stats[best] < min_frequency:
            break
        codes.append(best)
        vocab = merge_pair(best, vocab)
    return codes, vocab


def encode_word(word, codes):
    if not word:
        return tuple()
    symbols = word_to_symbols(word)
    ranks = {pair: rank for rank, pair in enumerate(codes)}
    while len(symbols) > 1:
        candidates = [(ranks[pair], pair) for pair in zip(symbols, symbols[1:]) if pair in ranks]
        if not candidates:
            break
        _, bigram = min(candidates)
        merged = []
        i = 0
        while i < len(symbols):
            if i < len(symbols) - 1 and (symbols[i], symbols[i + 1]) == bigram:
                merged.append(symbols[i] + symbols[i + 1])
                i += 2
            else:
                merged.append(symbols[i])
                i += 1
        symbols = tuple(merged)

    cleaned = list(symbols)
    if cleaned:
        if cleaned[-1] == "</w>":
            cleaned = cleaned[:-1]
        elif cleaned[-1].endswith("</w>"):
            cleaned[-1] = cleaned[-1][:-4]
    return tuple(piece for piece in cleaned if piece)


def segment_line(line, codes, separator):
    output = []
    for word in line.strip().split():
        pieces = encode_word(word, codes)
        if not pieces:
            continue
        for piece in pieces[:-1]:
            output.append(piece + separator)
        output.append(pieces[-1])
    return " ".join(output)


def code_lines(codes):
    return ["#version: 0.2"] + ["%s %s" % pair for pair in codes]


def write_outputs(write_dir, codes, encoded_lines):
    os.makedirs(write_dir, exist_ok=True)
    codes_path = os.path.join(write_dir, "codes.txt")
    encoded_path = os.path.join(write_dir, "encoded.txt")
    with open(codes_path, "w", encoding="utf-8") as f:
        f.write("\n".join(code_lines(codes)) + "\n")
    with open(encoded_path, "w", encoding="utf-8") as f:
        f.write("\n".join(encoded_lines) + "\n")
    return {"codes": codes_path, "encoded": encoded_path}


def main():
    args = parse_args()
    try:
        corpus, corpus_source = read_corpus(args.corpus)
        if not corpus:
            raise ValueError("learning corpus is empty")
        codes, final_vocab = learn_bpe(corpus, args.symbols, args.min_frequency)
        encode_inputs = args.encode if args.encode else list(DEFAULT_ENCODE)
        encoded = [segment_line(line, codes, args.separator) for line in encode_inputs]
        written = write_outputs(args.write_dir, codes, encoded) if args.write_dir else None
    except Exception as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1

    result = {
        "schema": "attention-is-all-you-need-pytorch.tiny-bpe-demo.v1",
        "corpus_source": corpus_source,
        "corpus_line_count": len(corpus),
        "symbols_requested": args.symbols,
        "min_frequency": args.min_frequency,
        "separator": args.separator,
        "codes": code_lines(codes),
        "encoded": [
            {"input": source, "output": output}
            for source, output in zip(encode_inputs, encoded)
        ],
        "final_vocab_size": len(final_vocab),
        "written": written,
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Tiny BPE demo")
        print("corpus_source:", result["corpus_source"])
        print("corpus_line_count:", result["corpus_line_count"])
        print("codes:")
        for line in result["codes"]:
            print("  " + line)
        print("encoded:")
        for item in result["encoded"]:
            print("  %r -> %r" % (item["input"], item["output"]))
        if written:
            print("written:")
            for key, path in written.items():
                print("  %s: %s" % (key, path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
