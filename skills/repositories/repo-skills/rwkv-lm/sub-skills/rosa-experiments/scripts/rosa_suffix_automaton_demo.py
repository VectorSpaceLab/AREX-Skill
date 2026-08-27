#!/usr/bin/env python3
"""Small CPU-only ROSA suffix-automaton behavior demo.

This adapts the compact `rosa` function used in RWKV-8 toy scripts. It prints,
for each position, the next symbol following the longest previous suffix when
one exists, otherwise -1.
"""
from __future__ import annotations

import argparse


def rosa(sequence: list[str]) -> list[str]:
    n = len(sequence)
    output = ["-1"] * n
    size = 2 * n + 1
    transitions = [None] * size
    suffix = [-1] * size
    length = [0] * size
    last_end = [-1] * size
    transitions[0] = {}
    active = 0
    next_state = 1
    for i, token in enumerate(sequence):
        current = next_state
        next_state += 1
        transitions[current] = {}
        length[current] = length[active] + 1
        p = active
        while p != -1 and token not in transitions[p]:
            transitions[p][token] = current
            p = suffix[p]
        if p == -1:
            suffix[current] = 0
        else:
            q = transitions[p][token]
            if length[p] + 1 == length[q]:
                suffix[current] = q
            else:
                clone = next_state
                next_state += 1
                transitions[clone] = transitions[q].copy()
                length[clone] = length[p] + 1
                suffix[clone] = suffix[q]
                last_end[clone] = last_end[q]
                while p != -1 and transitions[p].get(token) == q:
                    transitions[p][token] = clone
                    p = suffix[p]
                suffix[q] = suffix[current] = clone
        v = active = current
        answer = "-1"
        while v != -1:
            if length[v] > 0 and last_end[v] >= 0 and last_end[v] + 1 < n:
                answer = sequence[last_end[v] + 1]
                break
            v = suffix[v]
        output[i] = answer
        v = active
        while v != -1 and last_end[v] < i:
            last_end[v] = i
            v = suffix[v]
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sequence", help="Input sequence; use --split-chars or whitespace tokens")
    parser.add_argument("--split-chars", action="store_true", help="Treat every character as one token")
    args = parser.parse_args()
    tokens = list(args.sequence) if args.split_chars else args.sequence.split()
    if not tokens:
        raise SystemExit("no tokens supplied")
    out = rosa(tokens)
    print("input:", tokens)
    print("rosa:", out)


if __name__ == "__main__":
    main()
