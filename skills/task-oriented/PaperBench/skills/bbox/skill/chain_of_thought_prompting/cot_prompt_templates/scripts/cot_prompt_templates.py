#!/usr/bin/env python3
"""Prompt builders for chain-of-thought prompting experiments."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from typing import Any


VALID_MODES = {
    "standard",
    "chain_of_thought",
    "equation_only",
    "variable_compute_only",
    "reasoning_after_answer",
}
FINAL_MARKER = "The answer is"


@dataclass
class PromptResult:
    prompt: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"prompt": self.prompt, "metadata": self.metadata}


def _require_fields(exemplar: dict[str, Any], fields: list[str], index: int) -> None:
    for field in fields:
        value = str(exemplar.get(field, "")).strip()
        if not value:
            raise ValueError(f"exemplar {index} is missing required field {field!r}")


def _extract_equations(text: str) -> str:
    pieces = re.findall(r"[-+*/(). 0-9]+=\s*-?\d+(?:\.\d+)?", text)
    return ". ".join(piece.strip() for piece in pieces) or "Compute the needed quantities step by step."


def _render_exemplar(exemplar: dict[str, Any], mode: str, index: int) -> str:
    _require_fields(exemplar, ["question", "answer"], index)
    question = str(exemplar["question"]).strip()
    answer = str(exemplar["answer"]).strip().rstrip(".")

    if mode == "standard":
        body = f"{FINAL_MARKER} {answer}."
    else:
        _require_fields(exemplar, ["reasoning"], index)
        reasoning = str(exemplar["reasoning"]).strip().rstrip(".")
        if mode == "chain_of_thought":
            body = f"{reasoning}. {FINAL_MARKER} {answer}."
        elif mode == "equation_only":
            body = f"{_extract_equations(reasoning)}. {FINAL_MARKER} {answer}."
        elif mode == "variable_compute_only":
            body = f"We need to compute this carefully. {FINAL_MARKER} {answer}."
        elif mode == "reasoning_after_answer":
            body = f"{FINAL_MARKER} {answer}. Reasoning: {reasoning}."
        else:
            raise ValueError(f"unsupported mode: {mode}")
    return f"Q: {question}\nA: {body}"


def build_prompt(
    exemplars: list[dict[str, Any]],
    target_question: str,
    mode: str = "chain_of_thought",
    separator: str = "\n\n",
) -> PromptResult:
    """Render a few-shot prompt and metadata."""

    if mode not in VALID_MODES:
        raise ValueError(f"mode must be one of {sorted(VALID_MODES)}")
    if not exemplars:
        raise ValueError("at least one exemplar is required")
    target_question = str(target_question).strip()
    if not target_question:
        raise ValueError("target_question is required")

    rendered = [_render_exemplar(exemplar, mode, idx) for idx, exemplar in enumerate(exemplars)]
    rendered.append(f"Q: {target_question}\nA:")
    prompt = separator.join(rendered)
    metadata = {
        "mode": mode,
        "exemplar_count": len(exemplars),
        "reasoning_included": mode != "standard",
        "reasoning_precedes_answer": mode in {"chain_of_thought", "equation_only", "variable_compute_only"},
        "final_answer_marker": FINAL_MARKER,
        "target_answer_leaked": False,
    }
    return PromptResult(prompt=prompt, metadata=metadata)


def _self_test() -> None:
    exemplars = [
        {
            "question": "Roger has 5 balls and buys 2 cans of 3. How many?",
            "reasoning": "Roger buys 2 * 3 = 6 balls. 5 + 6 = 11",
            "answer": "11",
        }
    ]
    standard = build_prompt(exemplars, "Target?", "standard").to_dict()
    cot = build_prompt(exemplars, "Target?", "chain_of_thought").to_dict()
    assert "2 * 3 = 6" not in standard["prompt"]
    assert "2 * 3 = 6" in cot["prompt"]
    assert cot["prompt"].index("2 * 3 = 6") < cot["prompt"].index(FINAL_MARKER)
    assert cot["metadata"]["reasoning_precedes_answer"] is True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exemplars", help="JSON file containing exemplar list.")
    parser.add_argument("--target-question", default="")
    parser.add_argument("--mode", default="chain_of_thought", choices=sorted(VALID_MODES))
    parser.add_argument("--output", default="")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print(json.dumps({"ok": True}))
        return 0
    if not args.exemplars:
        raise SystemExit("--exemplars is required unless --self-test is used")
    with open(args.exemplars, "r", encoding="utf-8") as handle:
        exemplars = json.load(handle)
    result = build_prompt(exemplars, args.target_question, args.mode).to_dict()
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
