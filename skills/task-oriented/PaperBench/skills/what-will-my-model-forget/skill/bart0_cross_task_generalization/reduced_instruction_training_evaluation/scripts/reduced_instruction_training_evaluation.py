from __future__ import annotations

import math
import re
from typing import Any

TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(str(text).lower())


def rouge_l(prediction: str, reference: str) -> float:
    pred = tokens(prediction)
    ref = tokens(reference)
    if not pred or not ref:
        return 0.0
    dp = [[0] * (len(ref) + 1) for _ in range(len(pred) + 1)]
    for i, p in enumerate(pred, 1):
        for j, r in enumerate(ref, 1):
            dp[i][j] = dp[i-1][j-1] + 1 if p == r else max(dp[i-1][j], dp[i][j-1])
    lcs = dp[-1][-1]
    precision = lcs / len(pred)
    recall = lcs / len(ref)
    return 0.0 if precision + recall == 0 else (2 * precision * recall) / (precision + recall)


def score_candidate(candidate: str, instruction_text: str, instance_input: str, params: dict[str, float]) -> float:
    cand = set(tokens(candidate))
    instr = set(tokens(instruction_text))
    inp = set(tokens(instance_input))
    question_bonus = 1.0 if candidate.strip().endswith("?") else 0.0
    copy_penalty = len(cand & inp) / max(len(cand), 1)
    return (
        params.get("instruction_overlap", 0.0) * len(cand & instr)
        + params.get("input_overlap", 0.0) * len(cand & inp)
        + params.get("question_bonus", 0.0) * question_bonus
        - params.get("copy_penalty", 0.0) * copy_penalty
    )


def train_one_step(seen_item: dict[str, Any], params: dict[str, float], learning_rate: float = 0.2) -> dict[str, Any]:
    positive = seen_item["reference"]
    negative = seen_item["distractor"]
    instruction_text = seen_item["encoding"]
    instance_input = seen_item["input"]
    margin_before = score_candidate(positive, instruction_text, instance_input, params) - score_candidate(negative, instruction_text, instance_input, params)
    loss_before = max(0.0, 1.0 - margin_before)
    before = dict(params)
    if loss_before > 0:
        params = dict(params)
        params["question_bonus"] = params.get("question_bonus", 0.0) + learning_rate
        params["copy_penalty"] = params.get("copy_penalty", 0.0) + learning_rate / 2
        params["instruction_overlap"] = params.get("instruction_overlap", 0.0) + learning_rate / 4
    margin_after = score_candidate(positive, instruction_text, instance_input, params) - score_candidate(negative, instruction_text, instance_input, params)
    loss_after = max(0.0, 1.0 - margin_after)
    return {"loss_before": loss_before, "loss_after": loss_after, "params_before": before, "params_after": dict(params), "optimizer_state_changed": before != params}


def choose_prediction(candidates: list[str], instruction_text: str, instance_input: str, params: dict[str, float]) -> str:
    return max(candidates, key=lambda item: score_candidate(item, instruction_text, instance_input, params))
