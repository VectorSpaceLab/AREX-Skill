"""Ranking NCE objective and small finite optimizer."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Callable, Dict, List, Tuple


PROTOCOL_SCRIPTS = Path(__file__).resolve().parents[2] / "conditional_nce_protocol" / "scripts"
if str(PROTOCOL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PROTOCOL_SCRIPTS))

from conditional_nce_protocol import (  # noqa: E402
    ConditionalNCEProtocol,
    build_section_4_3_protocol,
    normalized_conditionals,
    section_4_3_score,
)


def _logsumexp(values: List[float]) -> float:
    top = max(values)
    return top + math.log(sum(math.exp(value - top) for value in values))


def section_4_3_score_from_params(params: Dict[str, float]) -> Callable[[str, str], float]:
    log_theta1 = float(params["log_theta1"])
    log_theta2 = float(params["log_theta2"])
    return lambda x_value, y_value: section_4_3_score(log_theta1, log_theta2, x_value, y_value)


def ranking_objective(protocol: ConditionalNCEProtocol, score_fn: Callable[[str, str], float]) -> float:
    total = 0.0
    for event in protocol.enumerate_population_events():
        x_value = event["x"]
        candidates = [event["positive"]] + list(event["negatives"])
        adjusted = [protocol.bar_score(score_fn(x_value, label), label) for label in candidates]
        total += float(event["probability"]) * (adjusted[0] - _logsumexp(adjusted))
    return total


def candidate_posterior(protocol: ConditionalNCEProtocol, score_fn: Callable[[str, str], float], x_value: str, candidates: List[str]) -> List[float]:
    adjusted = [protocol.bar_score(score_fn(x_value, label), label) for label in candidates]
    normalizer = _logsumexp(adjusted)
    return [math.exp(value - normalizer) for value in adjusted]


def ratio_from_params(protocol: ConditionalNCEProtocol, params: Dict[str, float], x_value: str = "x1") -> float:
    conditionals = normalized_conditionals(protocol, section_4_3_score_from_params(params))
    return conditionals[x_value]["y1"] / conditionals[x_value]["y2"]


def finite_difference_gradient(
    objective_fn: Callable[[Dict[str, float]], float],
    params: Dict[str, float],
    step: float = 1e-5,
) -> Dict[str, float]:
    gradient: Dict[str, float] = {}
    for key in sorted(params):
        plus = dict(params)
        minus = dict(params)
        plus[key] += step
        minus[key] -= step
        gradient[key] = (objective_fn(plus) - objective_fn(minus)) / (2.0 * step)
    return gradient


def optimize_section_4_3(
    k_negatives: int = 2,
    steps: int = 240,
    learning_rate: float = 0.2,
    start: Dict[str, float] | None = None,
) -> dict:
    protocol = build_section_4_3_protocol(k_negatives)
    params = dict(start or {"log_theta1": math.log(2.2), "log_theta2": math.log(1.2)})
    objective_fn = lambda p: ranking_objective(protocol, section_4_3_score_from_params(p))
    initial_params = dict(params)
    loss_before = -objective_fn(params)
    trace = []
    for step_index in range(steps):
        gradient = finite_difference_gradient(objective_fn, params)
        for key, value in gradient.items():
            params[key] += learning_rate * value
        if step_index in {0, steps - 1} or (step_index + 1) % max(1, steps // 4) == 0:
            trace.append(
                {
                    "step": step_index + 1,
                    "objective": objective_fn(params),
                    "ratio_x1": ratio_from_params(protocol, params),
                    "params": dict(params),
                }
            )
    loss_after = -objective_fn(params)
    conditionals = normalized_conditionals(protocol, section_4_3_score_from_params(params))
    posterior = candidate_posterior(protocol, section_4_3_score_from_params(params), "x1", ["y1", "y2"])
    return {
        "objective": objective_fn(params),
        "loss_before": loss_before,
        "loss_after": loss_after,
        "params_before": initial_params,
        "params_after": dict(params),
        "ratio_x1": conditionals["x1"]["y1"] / conditionals["x1"]["y2"],
        "true_ratio_x1": protocol.conditional_ratio("x1", "y1", "y2"),
        "conditionals": conditionals,
        "candidate_posterior_sum": sum(posterior),
        "trace": trace,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a small ranking NCE recovery on the Section 4.3 protocol.")
    parser.add_argument("--k", type=int, default=2)
    parser.add_argument("--steps", type=int, default=240)
    parser.add_argument("--learning-rate", type=float, default=0.2)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = optimize_section_4_3(args.k, args.steps, args.learning_rate)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "ratio_x1": result["ratio_x1"], "loss_after": result["loss_after"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
