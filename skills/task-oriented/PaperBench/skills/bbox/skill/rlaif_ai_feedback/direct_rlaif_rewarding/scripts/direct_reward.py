#!/usr/bin/env python3
"""Direct-RLAIF reward scoring from 1-to-10 score-token logits."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def stable_softmax(values: list[float]) -> list[float]:
    offset = max(values)
    exps = [math.exp(value - offset) for value in values]
    denom = sum(exps)
    return [value / denom for value in exps]


def build_direct_prompt(task: str, context: str, response: str) -> str:
    if task == "summarization":
        preamble = "You are an expert summary rater. Provide a SCORE from 1 to 10 for the SUMMARY given the TEXT."
        return f"{preamble}\nTEXT: {context}\nSUMMARY: {response}\nSCORE:"
    if task == "helpful_dialogue":
        preamble = "You are an expert rater of helpful and honest Assistant responses. Provide a SCORE from 1 to 10."
        return f"{preamble}\nCONTEXT: {context}\nRESPONSE: {response}\nSCORE:"
    raise ValueError(f"unsupported direct-RLAIF task: {task}")


class HeuristicDirectScorer:
    def logits(self, context: str, response: str) -> dict[str, float]:
        context_terms = {
            token.strip(".,!?;:()[]{}'\"").lower()
            for token in context.split()
            if len(token.strip(".,!?;:()[]{}'\"")) > 3
        }
        response_terms = [token.strip(".,!?;:()[]{}'\"").lower() for token in response.split()]
        overlap = sum(1 for token in response_terms if token in context_terms)
        length = min(len(response_terms), 70)
        raw_score = max(1.0, min(10.0, 1.0 + 0.9 * overlap + 0.03 * length))
        return {str(score): -abs(float(score) - raw_score) for score in range(1, 11)}


def score_direct_reward(task: str, context: str, response: str, scorer: HeuristicDirectScorer | None = None) -> dict:
    scorer = scorer or HeuristicDirectScorer()
    prompt = build_direct_prompt(task, context, response)
    logits = scorer.logits(context, response)
    missing = [str(score) for score in range(1, 11) if str(score) not in logits]
    if missing:
        raise ValueError("missing score-token logits: " + ", ".join(missing))
    ordered_logits = [float(logits[str(score)]) for score in range(1, 11)]
    probabilities = stable_softmax(ordered_logits)
    expected = sum(score * prob for score, prob in zip(range(1, 11), probabilities))
    normalized = ((expected - 1.0) / 9.0) * 2.0 - 1.0
    normalized = max(-1.0, min(1.0, normalized))
    return {
        "task": task,
        "prompt": prompt,
        "score_logits": logits,
        "score_probabilities": {str(score): probabilities[score - 1] for score in range(1, 11)},
        "expected_score": expected,
        "normalized_reward": normalized,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.smoke or not args.input:
        result = score_direct_reward(
            "summarization",
            "A student bought a used computer and monitor mostly with their own money.",
            "I bought a used computer and monitor mostly with my own money.",
        )
    else:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        result = score_direct_reward(data["task"], data["context"], data["response"])
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
