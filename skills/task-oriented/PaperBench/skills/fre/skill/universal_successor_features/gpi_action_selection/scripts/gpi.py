#!/usr/bin/env python3
"""Generalized policy improvement over USFA candidate encodings."""

from __future__ import annotations

import argparse
import json
from typing import Dict, List, Mapping, Sequence, Tuple

PsiTable = Mapping[str, Mapping[str, Mapping[str, Sequence[float]]]]


def encoding_key(encoding: Sequence[float]) -> str:
    return ",".join(f"{float(value):.6f}" for value in encoding)


def dot(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("dimension mismatch")
    return sum(float(a) * float(b) for a, b in zip(left, right))


def lookup_psi(table: PsiTable, state: str, action: str, encoding: Sequence[float]) -> List[float]:
    return [float(value) for value in table[state][action][encoding_key(encoding)]]


def gpi_select(table: PsiTable, state: str, actions: Sequence[str], target_w: Sequence[float], candidates: Sequence[Sequence[float]]) -> Dict[str, object]:
    if not actions:
        raise ValueError("actions must not be empty")
    if not candidates:
        raise ValueError("candidates must not be empty")
    action_scores: Dict[str, Dict[str, object]] = {}
    for action in actions:
        candidate_scores: List[Dict[str, object]] = []
        for candidate in candidates:
            score = dot(lookup_psi(table, state, action, candidate), target_w)
            candidate_scores.append({"candidate": [float(value) for value in candidate], "score": score})
        best = max(candidate_scores, key=lambda item: (float(item["score"]), -candidate_scores.index(item)))
        action_scores[action] = {"best_score": best["score"], "best_candidate": best["candidate"], "candidate_scores": candidate_scores}
    best_action = max(actions, key=lambda action: (float(action_scores[action]["best_score"]), -actions.index(action)))
    return {
        "action": best_action,
        "score": action_scores[best_action]["best_score"],
        "winning_candidate": action_scores[best_action]["best_candidate"],
        "action_scores": action_scores,
        "candidate_count": len(candidates),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--table-json", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--actions", nargs="+", required=True)
    parser.add_argument("--target-w", nargs="+", type=float, required=True)
    parser.add_argument("--candidates-json", required=True)
    args = parser.parse_args()
    with open(args.table_json, "r", encoding="utf-8") as handle:
        table = json.load(handle)
    with open(args.candidates_json, "r", encoding="utf-8") as handle:
        candidates = json.load(handle)
    print(json.dumps(gpi_select(table, args.state, args.actions, args.target_w, candidates), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
