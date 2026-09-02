#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from typing import Any, Sequence


def flatten(values: Sequence[Any]) -> list[float]:
    out: list[float] = []
    for value in values:
        if isinstance(value, (list, tuple)):
            out.extend(flatten(value))
        else:
            out.append(float(value))
    return out


def relative_l2(prediction: Sequence[Any], target: Sequence[Any], eps: float = 1e-12) -> float:
    pred = flatten(prediction)
    truth = flatten(target)
    if len(pred) != len(truth) or not pred:
        raise ValueError("prediction and target must have the same non-empty flattened length")
    numerator = math.sqrt(sum((a - b) ** 2 for a, b in zip(pred, truth)))
    denominator = max(math.sqrt(sum(b ** 2 for b in truth)), eps)
    return numerator / denominator


def absolute_l2(prediction: Sequence[Any], target: Sequence[Any]) -> float:
    pred = flatten(prediction)
    truth = flatten(target)
    if len(pred) != len(truth) or not pred:
        raise ValueError("prediction and target must have the same non-empty flattened length")
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(pred, truth)) / len(pred))


def summarize(prediction: Sequence[Any], target: Sequence[Any], loss_trace: list[float] | None = None, threshold: float = 0.5) -> dict[str, Any]:
    rel = relative_l2(prediction, target)
    abs_err = absolute_l2(prediction, target)
    finite_trace = all(math.isfinite(float(x)) for x in (loss_trace or []))
    improved = bool(loss_trace and len(loss_trace) >= 2 and loss_trace[-1] < loss_trace[0])
    return {
        "relative_l2_error": rel,
        "absolute_l2_error": abs_err,
        "high_relative_error": rel > threshold,
        "loss_trace_finite": finite_trace,
        "loss_improved": improved,
        "summary": f"relative_l2={rel:.6g}, absolute_l2={abs_err:.6g}, high_error={rel > threshold}"
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("prediction_json")
    parser.add_argument("target_json")
    args = parser.parse_args()
    prediction = json.load(open(args.prediction_json, "r", encoding="utf-8"))
    target = json.load(open(args.target_json, "r", encoding="utf-8"))
    print(json.dumps(summarize(prediction, target), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
