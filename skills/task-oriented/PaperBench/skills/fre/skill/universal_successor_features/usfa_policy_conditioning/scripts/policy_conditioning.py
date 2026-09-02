#!/usr/bin/env python3
"""Policy-conditioning helpers for tabular USFA experiments."""

from __future__ import annotations

import argparse
import json
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

Encoding = Tuple[float, ...]
PsiTable = Mapping[str, Mapping[str, Mapping[str, Sequence[float]]]]


def canonical_encoding(values: Iterable[float], precision: int = 6) -> Encoding:
    encoding = tuple(round(float(value), precision) for value in values)
    if not encoding:
        raise ValueError("encoding must not be empty")
    return encoding


def encoding_key(encoding: Sequence[float]) -> str:
    return ",".join(f"{float(value):.6f}" for value in encoding)


def build_candidate_set(*groups: Iterable[Iterable[float]]) -> List[Encoding]:
    seen = set()
    candidates: List[Encoding] = []
    for group in groups:
        for values in group:
            encoding = canonical_encoding(values)
            if encoding not in seen:
                seen.add(encoding)
                candidates.append(encoding)
    if not candidates:
        raise ValueError("candidate set must not be empty")
    return candidates


def dot(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("dimension mismatch")
    return sum(float(a) * float(b) for a, b in zip(left, right))


def lookup_psi(table: PsiTable, state: str, action: str, encoding: Sequence[float]) -> List[float]:
    key = encoding_key(encoding)
    try:
        return [float(value) for value in table[state][action][key]]
    except KeyError as exc:
        raise KeyError(f"missing psi for state={state} action={action} z={key}") from exc


def greedy_action_for_encoding(table: PsiTable, state: str, actions: Sequence[str], encoding: Sequence[float]) -> Dict[str, object]:
    if not actions:
        raise ValueError("actions must not be empty")
    scores = {}
    for action in actions:
        scores[action] = dot(lookup_psi(table, state, action, encoding), encoding)
    best_action = max(actions, key=lambda action: (scores[action], -actions.index(action)))
    return {"action": best_action, "scores": scores, "encoding": list(canonical_encoding(encoding))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--table-json", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--actions", nargs="+", required=True)
    parser.add_argument("--z", nargs="+", type=float, required=True)
    args = parser.parse_args()
    with open(args.table_json, "r", encoding="utf-8") as handle:
        table = json.load(handle)
    print(json.dumps(greedy_action_for_encoding(table, args.state, args.actions, args.z), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
