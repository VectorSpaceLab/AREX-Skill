#!/usr/bin/env python3
"""Select GSM8K predictions from verifier-scored candidates."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def group_candidates(candidates: list[dict]) -> dict[str, list[dict]]:
    grouped = defaultdict(list)
    for candidate in candidates:
        grouped[str(candidate["problem_id"])].append(candidate)
    return dict(grouped)


def ranked(candidates: list[dict]) -> list[dict]:
    return sorted(candidates, key=lambda item: (-float(item.get("verifier_score", 0.0)), str(item.get("candidate_id", ""))))


def select_predictions(candidates: list[dict], mode: str = "top_score", top_k: int = 3) -> list[dict]:
    predictions = []
    for problem_id, items in sorted(group_candidates(candidates).items()):
        ordered = ranked(items)
        if mode == "top_score":
            selected = ordered[0]
            vote_counts = Counter([selected.get("extracted_answer", "[invalid]")])
        elif mode == "top_k_vote":
            top_items = ordered[: max(1, top_k)]
            vote_counts = Counter(item.get("extracted_answer", "[invalid]") for item in top_items)
            best_answer = sorted(
                vote_counts,
                key=lambda answer: (
                    -vote_counts[answer],
                    -max(float(item.get("verifier_score", 0.0)) for item in top_items if item.get("extracted_answer", "[invalid]") == answer),
                    str(answer),
                ),
            )[0]
            selected = next(item for item in top_items if item.get("extracted_answer", "[invalid]") == best_answer)
        else:
            raise ValueError(f"unknown selection mode: {mode}")
        predictions.append(
            {
                "problem_id": problem_id,
                "selected_candidate_id": selected.get("candidate_id"),
                "selected_answer": selected.get("extracted_answer", "[invalid]"),
                "gold_answer": selected.get("gold_answer"),
                "selected_score": selected.get("verifier_score"),
                "mode": mode,
                "top_k": top_k if mode == "top_k_vote" else 1,
                "vote_counts": dict(vote_counts),
                "ranking": [
                    {
                        "candidate_id": item.get("candidate_id"),
                        "answer": item.get("extracted_answer"),
                        "score": item.get("verifier_score"),
                    }
                    for item in ordered
                ],
            }
        )
    return predictions


def write_predictions(scored_path: str, output_path: str, mode: str, top_k: int) -> dict:
    candidates = json.loads(Path(scored_path).read_text(encoding="utf-8"))
    predictions = select_predictions(candidates, mode=mode, top_k=top_k)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(predictions, indent=2) + "\n", encoding="utf-8")
    return {"prediction_count": len(predictions), "mode": mode}


def self_test() -> None:
    candidates = [
        {"problem_id": "0", "candidate_id": "0_a", "extracted_answer": "1", "gold_answer": "1", "verifier_score": 0.9},
        {"problem_id": "0", "candidate_id": "0_b", "extracted_answer": "2", "gold_answer": "1", "verifier_score": 0.8},
        {"problem_id": "0", "candidate_id": "0_c", "extracted_answer": "2", "gold_answer": "1", "verifier_score": 0.7},
    ]
    assert select_predictions(candidates, "top_score")[0]["selected_answer"] == "1"
    assert select_predictions(candidates, "top_k_vote", top_k=3)[0]["selected_answer"] == "2"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_select = sub.add_parser("select")
    p_select.add_argument("--scored", required=True)
    p_select.add_argument("--output", required=True)
    p_select.add_argument("--mode", choices=["top_score", "top_k_vote"], default="top_score")
    p_select.add_argument("--top-k", type=int, default=3)
    sub.add_parser("self-test")
    args = parser.parse_args(argv)
    if args.cmd == "select":
        result = write_predictions(args.scored, args.output, args.mode, args.top_k)
        print(json.dumps(result, indent=2))
    elif args.cmd == "self-test":
        self_test()
        print(json.dumps({"ok": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
