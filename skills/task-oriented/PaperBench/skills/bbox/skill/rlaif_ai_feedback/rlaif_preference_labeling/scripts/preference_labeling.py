#!/usr/bin/env python3
"""Deterministic utilities for RLAIF pairwise AI preference labeling."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Callable, Iterable


TASK_PREAMBLES = {
    "summarization": "You are an expert summary rater. Choose the better summary for the given text.",
    "helpful_dialogue": "You are an expert rater of helpful and honest assistant responses.",
    "harmless_dialogue": "You are an expert rater of harmful assistant responses. Choose the more harmful response.",
}


def stable_softmax(values: Iterable[float]) -> list[float]:
    values = [float(value) for value in values]
    if not values:
        raise ValueError("softmax requires at least one value")
    offset = max(values)
    exps = [math.exp(value - offset) for value in values]
    denom = sum(exps)
    return [value / denom for value in exps]


def build_prompt(
    task: str,
    context: str,
    response1: str,
    response2: str,
    *,
    detailed: bool = False,
    rationale: str = "",
    ending: str = "Preferred Response=",
) -> str:
    if task not in TASK_PREAMBLES:
        raise ValueError(f"unsupported task: {task}")
    preamble = TASK_PREAMBLES[task]
    if detailed and task == "summarization":
        preamble += " Consider coherence, accuracy, coverage, and overall quality."
    parts = [
        preamble,
        f"Context - {context}",
        f"Response 1 - {response1}",
        f"Response 2 - {response2}",
    ]
    if rationale:
        parts.append(f"Rationale: {rationale}")
    parts.append(ending)
    return "\n".join(parts)


class LabelerResult:
    logits: dict[str, float]

    def __init__(self, logits: dict[str, float], rationale: str = "") -> None:
        self.logits = logits
        self.rationale = rationale


class HeuristicLabeler:
    """Tiny deterministic labeler used for tests and reduced recovery."""

    def __init__(self, position_bias: float = 0.0) -> None:
        self.position_bias = float(position_bias)

    @staticmethod
    def _quality(text: str, context: str) -> float:
        tokens = [token.strip(".,!?;:()[]{}'\"").lower() for token in text.split()]
        context_tokens = {
            token.strip(".,!?;:()[]{}'\"").lower()
            for token in context.split()
            if len(token.strip(".,!?;:()[]{}'\"")) > 3
        }
        overlap = sum(1 for token in tokens if token in context_tokens)
        length_bonus = min(len(tokens), 60) / 60.0
        detail_bonus = sum(1 for marker in ["because", "but", "without", "wants", "legal", "insurance"] if marker in tokens)
        return overlap + 0.5 * length_bonus + 0.25 * detail_bonus

    def score(self, prompt: str, context: str, response1: str, response2: str, *, want_rationale: bool = False) -> LabelerResult:
        q1 = self._quality(response1, context)
        q2 = self._quality(response2, context)
        rationale = ""
        if want_rationale:
            better = "1" if q1 >= q2 else "2"
            rationale = f"Response {better} better matches the context with more relevant detail."
        return LabelerResult(
            logits={
                "1": q1 + self.position_bias,
                "2": q2,
            },
            rationale=rationale,
        )


def label_pair(
    task: str,
    context: str,
    response1: str,
    response2: str,
    labeler: HeuristicLabeler | Callable[..., LabelerResult],
    *,
    detailed: bool = False,
    chain_of_thought: bool = False,
    mitigate_position_bias: bool = True,
) -> dict:
    records = []

    def run_once(display_response1: str, display_response2: str, swapped: bool) -> list[float]:
        rationale = ""
        if chain_of_thought:
            cot_prompt = build_prompt(
                task,
                context,
                display_response1,
                display_response2,
                detailed=detailed,
                ending="Explain which response is better. Rationale:",
            )
            cot_result = labeler.score(cot_prompt, context, display_response1, display_response2, want_rationale=True)
            rationale = cot_result.rationale
        prompt = build_prompt(
            task,
            context,
            display_response1,
            display_response2,
            detailed=detailed,
            rationale=rationale,
        )
        result = labeler.score(prompt, context, display_response1, display_response2, want_rationale=False)
        probs_display = stable_softmax([result.logits["1"], result.logits["2"]])
        if swapped:
            probs_original = [probs_display[1], probs_display[0]]
        else:
            probs_original = list(probs_display)
        records.append(
            {
                "swapped": swapped,
                "prompt": prompt,
                "rationale": rationale,
                "logits": dict(result.logits),
                "probabilities_display_order": probs_display,
                "probabilities_original_order": probs_original,
            }
        )
        return probs_original

    distributions = [run_once(response1, response2, False)]
    if mitigate_position_bias:
        distributions.append(run_once(response2, response1, True))
    preference = [
        sum(item[0] for item in distributions) / len(distributions),
        sum(item[1] for item in distributions) / len(distributions),
    ]
    total = sum(preference)
    preference = [value / total for value in preference]
    return {
        "task": task,
        "preference": preference,
        "argmax_label": 1 if preference[0] >= preference[1] else 2,
        "records": records,
    }


def smoke() -> dict:
    labeler = HeuristicLabeler(position_bias=0.4)
    return label_pair(
        "summarization",
        "A student bought a used computer and monitor with mostly their own money; their mother wants it returned.",
        "I bought a gaming PC and my mother is angry.",
        "I bought a used computer and monitor mostly with my own money, and my mother wants me to return it.",
        labeler,
        detailed=True,
        chain_of_thought=True,
        mitigate_position_bias=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="", help="Optional JSON input with task/context/response1/response2.")
    parser.add_argument("--output", default="", help="Optional output JSON path.")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    if args.smoke or not args.input:
        result = smoke()
    else:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        result = label_pair(
            data["task"],
            data["context"],
            data["response1"],
            data["response2"],
            HeuristicLabeler(position_bias=float(data.get("position_bias", 0.0))),
            detailed=bool(data.get("detailed", False)),
            chain_of_thought=bool(data.get("chain_of_thought", False)),
            mitigate_position_bias=bool(data.get("mitigate_position_bias", True)),
        )
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
