#!/usr/bin/env python3
"""Service-free smoke checks for AdalFlow evaluation metrics.

This script intentionally avoids provider calls, dataset downloads, and benchmark runs.
It verifies exact/fuzzy/F1 answer matching plus retriever recall/precision shapes.
"""

from __future__ import annotations

import json
import math
from typing import Iterable, Sequence

from adalflow.eval import AnswerMatchAcc, RetrieverEvaluator
from adalflow.optim import Parameter


def _assert_close(actual: float, expected: float, *, label: str) -> None:
    if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12):
        raise AssertionError(f"{label}: expected {expected}, got {actual}")


def _assert_sequence_close(
    actual: Sequence[float], expected: Sequence[float], *, label: str
) -> None:
    if len(actual) != len(expected):
        raise AssertionError(f"{label}: expected length {len(expected)}, got {len(actual)}")
    for index, (left, right) in enumerate(zip(actual, expected)):
        _assert_close(left, right, label=f"{label}[{index}]")


def _as_float_list(values: Iterable[float]) -> list[float]:
    return [float(value) for value in values]


def main() -> None:
    pred_answers = ["positive", "negative", "this is neutral"]
    gt_answers = ["positive", "negative", "neutral"]

    exact_result = AnswerMatchAcc(type="exact_match").compute(pred_answers, gt_answers)
    _assert_close(exact_result.avg_score, 2 / 3, label="exact avg")
    _assert_sequence_close(
        exact_result.per_item_scores, [1.0, 1.0, 0.0], label="exact scores"
    )

    fuzzy_result = AnswerMatchAcc(type="fuzzy_match").compute(pred_answers, gt_answers)
    _assert_close(fuzzy_result.avg_score, 1.0, label="fuzzy avg")
    _assert_sequence_close(
        fuzzy_result.per_item_scores, [1.0, 1.0, 1.0], label="fuzzy scores"
    )

    parameter_score = AnswerMatchAcc(type="exact_match").compute_single_item(
        Parameter(data="The Answer", requires_opt=False, role_desc="prediction"),
        Parameter(data="answer", requires_opt=False, role_desc="ground truth"),
    )
    _assert_close(parameter_score, 1.0, label="parameter exact score")

    f1_score = AnswerMatchAcc(type="f1_score").compute_single_item(
        "blue car", "blue truck"
    )
    _assert_close(f1_score, 0.5, label="token f1 score")

    retrieved_contexts = [
        ["Apple is founded before Google."],
        [
            "Feburary has 28 days in common years.",
            "Feburary has 29 days in leap years.",
            "Feburary is the second month of the year.",
        ],
    ]
    gt_contexts = [
        [
            "Apple is founded in 1976.",
            "Google is founded in 1998.",
            "Apple is founded before Google.",
        ],
        [
            "Feburary has 28 days in common years",
            "Feburary has 29 days in leap years",
        ],
    ]
    retriever_result = RetrieverEvaluator().compute(retrieved_contexts, gt_contexts)
    _assert_close(retriever_result["avg_recall"], 2 / 3, label="retriever recall")
    _assert_close(
        retriever_result["avg_precision"], 0.8333333333333333, label="retriever precision"
    )
    _assert_sequence_close(
        retriever_result["recall_list"], [1 / 3, 1.0], label="retriever recall list"
    )
    _assert_sequence_close(
        retriever_result["precision_list"],
        [1.0, 2 / 3],
        label="retriever precision list",
    )

    summary = {
        "answer_exact_avg": float(exact_result.avg_score),
        "answer_fuzzy_avg": float(fuzzy_result.avg_score),
        "parameter_exact_score": float(parameter_score),
        "token_f1_score": float(f1_score),
        "retriever_avg_recall": float(retriever_result["avg_recall"]),
        "retriever_avg_precision": float(retriever_result["avg_precision"]),
        "retriever_recall_list": _as_float_list(retriever_result["recall_list"]),
        "retriever_precision_list": _as_float_list(
            retriever_result["precision_list"]
        ),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
