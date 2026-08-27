#!/usr/bin/env python3
"""Learn tiny BPE merge additions in Qwen tiktoken format.

This adapts the repository's merge-extension idea for safe local use. It reads a
base tiktoken BPE file and a TSV of `word<TAB>frequency`, then writes only the
new merges. It does not edit checkpoints or load models.
"""
from __future__ import annotations

import argparse
import base64
import collections
from pathlib import Path


def load_tiktoken_bpe(path: Path) -> dict[bytes, int]:
    ranks: dict[bytes, int] = {}
    for line in path.read_bytes().splitlines():
        if not line:
            continue
        token, rank = line.split()
        ranks[base64.b64decode(token)] = int(rank)
    return ranks


def bytes_to_pieces(b: bytes) -> tuple[bytes, ...]:
    return tuple(bytes([x]) for x in b)


def apply_pair(pieces: tuple[bytes, ...], pair: tuple[bytes, bytes]) -> tuple[bytes, ...]:
    out = []
    i = 0
    while i < len(pieces):
        if i < len(pieces) - 1 and pieces[i] == pair[0] and pieces[i + 1] == pair[1]:
            out.append(pair[0] + pair[1])
            i += 2
        else:
            out.append(pieces[i])
            i += 1
    return tuple(out)


def bpe(word: bytes, merges: dict[bytes, int]) -> tuple[bytes, ...]:
    pieces = bytes_to_pieces(word)
    while len(pieces) > 1:
        pairs = list(zip(pieces[:-1], pieces[1:]))
        best = min(pairs, key=lambda p: merges.get(p[0] + p[1], 10**18))
        if best[0] + best[1] not in merges:
            break
        pieces = apply_pair(pieces, best)
    return pieces


def learn(freqs: dict[str, int], existing: dict[bytes, int], limit: int) -> list[bytes]:
    vocab = {bpe(word.encode("utf-8"), existing): freq for word, freq in freqs.items()}
    new = []
    for _ in range(limit):
        stats: collections.Counter[tuple[bytes, bytes]] = collections.Counter()
        for pieces, freq in vocab.items():
            if len(pieces) > 1:
                for pair in zip(pieces[:-1], pieces[1:]):
                    stats[pair] += freq
        if not stats:
            break
        pair, _freq = max(stats.items(), key=lambda x: (x[1], -len(x[0][0] + x[0][1])))
        merged = pair[0] + pair[1]
        if merged in existing:
            break
        new.append(merged)
        existing[merged] = max(existing.values(), default=0) + 1
        vocab = {apply_pair(pieces, pair): freq for pieces, freq in vocab.items()}
    return new


def main() -> int:
    p = argparse.ArgumentParser(description="Create a small Qwen-compatible new-merge file from word frequencies.")
    p.add_argument("input_path")
    p.add_argument("output_path")
    p.add_argument("vocab_path", help="TSV: word<TAB>frequency")
    p.add_argument("--start-id", type=int, default=151851)
    p.add_argument("--limit", type=int, default=100)
    args = p.parse_args()
    existing = load_tiktoken_bpe(Path(args.input_path))
    freqs = {}
    for line in Path(args.vocab_path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        word, freq = line.split("\t", 1)
        freqs[word] = int(freq)
    new_merges = learn(freqs, dict(existing), args.limit)
    with Path(args.output_path).open("wb") as f:
        for i, token in enumerate(new_merges, start=args.start_id):
            f.write(base64.b64encode(token) + b" " + str(i).encode() + b"\n")
    print(f"wrote {len(new_merges)} merges to {args.output_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
