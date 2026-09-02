#!/usr/bin/env python3
"""ALICE-style weighted classifier-in-the-loop candidate scoring."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path


def target_class(prompt_label: str, attack: str) -> str:
    label = prompt_label.lower()
    if label in {"hate", "hateful"}:
        label = "toxic"
    if label in {"neutral", "non_toxic", "nontoxic"}:
        label = "benign"
    attack = attack.lower()
    if attack in {"false_negative", "detoxify"}:
        return "benign"
    if attack == "false_positive":
        return "toxic"
    if attack == "match_prompt":
        return label
    raise ValueError(f"unsupported attack mode: {attack!r}")


def prompt_terms(prompt: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[a-zA-Z][a-zA-Z0-9_'-]*", prompt)}


def copied_from_prompt(candidate: str, prompt: str) -> bool:
    words = [token.lower() for token in re.findall(r"[a-zA-Z][a-zA-Z0-9_'-]*", candidate)]
    terms = prompt_terms(prompt)
    return bool(words) and all(word in terms for word in words)


def score_candidates(
    prompt: str,
    candidates: list[dict],
    prompt_label: str,
    attack: str,
    lambda_l: float = 0.5,
    lambda_c: float = 0.5,
    beam_size: int = 1,
    prevent_prompt_copy: bool = True,
) -> dict:
    target = target_class(prompt_label, attack)
    trace = []
    for index, item in enumerate(candidates):
        text = str(item["text"])
        lm_logprob = float(item["lm_logprob"])
        clf = item.get("classifier_logprobs") or {}
        if target not in clf:
            raise ValueError(f"candidate {index} lacks classifier score for {target}")
        classifier_logprob = float(clf[target])
        excluded = prevent_prompt_copy and copied_from_prompt(text, prompt)
        combined = -math.inf if excluded else lambda_l * lm_logprob + lambda_c * classifier_logprob
        trace.append(
            {
                "index": index,
                "text": text,
                "lm_logprob": lm_logprob,
                "target_class": target,
                "classifier_logprob": classifier_logprob,
                "combined_score": combined,
                "excluded": excluded,
                "excluded_reason": "prompt_copy" if excluded else "",
            }
        )
    ranked = sorted(trace, key=lambda row: row["combined_score"], reverse=True)
    beams = ranked[:beam_size]
    selected = beams[0] if beams else None
    return {
        "schema_version": 1,
        "prompt_label": prompt_label,
        "attack": attack,
        "target_class": target,
        "lambda_l": lambda_l,
        "lambda_c": lambda_c,
        "beam_size": beam_size,
        "prevent_prompt_copy": prevent_prompt_copy,
        "selected": selected,
        "beams": beams,
        "trace": trace,
        "mechanism_checks": {
            "weighted_alice_score_used": True,
            "classifier_target_class": target,
            "prompt_copy_prevention_used": prevent_prompt_copy,
        },
    }


def run_self_test() -> None:
    candidates = [
        {"text": "the prompt", "lm_logprob": -0.01, "classifier_logprobs": {"benign": -0.01, "toxic": -5.0}},
        {"text": "a coded stereotype appears", "lm_logprob": -2.0, "classifier_logprobs": {"benign": -0.1, "toxic": -4.0}},
        {"text": "a plain sentence appears", "lm_logprob": -0.5, "classifier_logprobs": {"benign": -2.0, "toxic": -0.2}},
    ]
    result = score_candidates("the prompt", candidates, "toxic", "false_negative", lambda_l=0.2, lambda_c=0.8)
    assert result["target_class"] == "benign"
    assert result["selected"]["text"] == "a coded stereotype appears"
    assert result["trace"][0]["excluded"] is True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", default="")
    parser.add_argument("--output-json", default="")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        run_self_test()
        print(json.dumps({"ok": True, "test": "alice_decoding"}))
        return 0
    if not args.input_json or not args.output_json:
        parser.error("--input-json and --output-json are required unless --self-test is used")
    payload = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    result = score_candidates(
        payload["prompt"],
        payload["candidates"],
        payload["prompt_label"],
        payload.get("attack", "false_negative"),
        float(payload.get("lambda_l", 0.5)),
        float(payload.get("lambda_c", 0.5)),
        int(payload.get("beam_size", 1)),
        bool(payload.get("prevent_prompt_copy", True)),
    )
    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_json).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"selected": result["selected"], "target_class": result["target_class"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
