#!/usr/bin/env python3
"""Deterministic DeBERTa-style disentangled attention helpers."""

from __future__ import annotations

import argparse
import json
import math
from typing import Iterable


def token_feature(token: str) -> float:
    """Map a token to a stable scalar content feature."""
    letters = [ord(ch.lower()) - 96 for ch in token if ch.isalpha()]
    if not letters:
        return 0.1
    return sum(letters) / (26.0 * len(letters))


def relative_index(query_index: int, key_index: int, max_relative_distance: int) -> int:
    if max_relative_distance < 1:
        raise ValueError("max_relative_distance must be positive")
    raw = query_index - key_index
    if raw <= -max_relative_distance:
        return 0
    if raw >= max_relative_distance:
        return 2 * max_relative_distance - 1
    return raw + max_relative_distance


def relative_index_matrix(length: int, max_relative_distance: int) -> list[list[int]]:
    if length < 0:
        raise ValueError("length must be non-negative")
    return [
        [relative_index(i, j, max_relative_distance) for j in range(length)]
        for i in range(length)
    ]


def _distance_center(index: int, max_relative_distance: int) -> float:
    center = max_relative_distance
    return (index - center) / max(1.0, float(max_relative_distance))


def compute_attention(
    tokens: Iterable[str],
    max_relative_distance: int = 2,
    active_terms: Iterable[str] = ("c2c", "c2p", "p2c"),
) -> dict:
    token_list = list(tokens)
    features = [token_feature(token) for token in token_list]
    active = set(active_terms)
    rel = relative_index_matrix(len(token_list), max_relative_distance)
    components = {
        "c2c": [],
        "c2p": [],
        "p2c": [],
    }
    combined: list[list[float]] = []
    for i, query_value in enumerate(features):
        row = []
        c2c_row = []
        c2p_row = []
        p2c_row = []
        for j, key_value in enumerate(features):
            c2c = query_value * key_value
            c2p = query_value * _distance_center(rel[i][j], max_relative_distance)
            reverse_index = relative_index(j, i, max_relative_distance)
            p2c = key_value * _distance_center(reverse_index, max_relative_distance)
            c2c_row.append(c2c)
            c2p_row.append(c2p)
            p2c_row.append(p2c)
            total = 0.0
            count = 0
            for name, value in [("c2c", c2c), ("c2p", c2p), ("p2c", p2c)]:
                if name in active:
                    total += value
                    count += 1
            scale = math.sqrt(max(count, 1))
            row.append(total / scale)
        components["c2c"].append(c2c_row)
        components["c2p"].append(c2p_row)
        components["p2c"].append(p2c_row)
        combined.append(row)
    return {
        "tokens": token_list,
        "features": features,
        "max_relative_distance": max_relative_distance,
        "active_terms": sorted(active),
        "relative_index_matrix": rel,
        "components": components,
        "combined": combined,
        "row_sums": [sum(row) for row in combined],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tokens", nargs="+", required=True)
    parser.add_argument("--max-relative-distance", type=int, default=2)
    parser.add_argument("--terms", default="c2c,c2p,p2c")
    args = parser.parse_args()
    result = compute_attention(
        args.tokens,
        max_relative_distance=args.max_relative_distance,
        active_terms=[item.strip() for item in args.terms.split(",") if item.strip()],
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
