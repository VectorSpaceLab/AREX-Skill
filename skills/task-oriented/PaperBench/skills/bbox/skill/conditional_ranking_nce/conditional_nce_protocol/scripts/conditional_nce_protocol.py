"""Finite conditional NCE protocol helpers."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
import json
import math
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple


ProbabilityTable = Dict[str, float]
NestedProbabilityTable = Dict[str, ProbabilityTable]


def _check_distribution(name: str, table: ProbabilityTable, support: Iterable[str]) -> None:
    labels = list(support)
    missing = [item for item in labels if item not in table]
    if missing:
        raise ValueError(f"{name} is missing support entries: {missing}")
    total = sum(float(table[item]) for item in labels)
    if not math.isclose(total, 1.0, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError(f"{name} must sum to 1.0, got {total}")
    bad = [item for item in labels if float(table[item]) < 0.0]
    if bad:
        raise ValueError(f"{name} has negative probabilities: {bad}")


@dataclass(frozen=True)
class ConditionalNCEProtocol:
    inputs: Tuple[str, ...]
    labels: Tuple[str, ...]
    p_x: NestedProbabilityTable | ProbabilityTable
    p_y_given_x: NestedProbabilityTable
    p_noise: ProbabilityTable
    k_negatives: int

    def __post_init__(self) -> None:
        if self.k_negatives < 1:
            raise ValueError("k_negatives must be at least 1")
        _check_distribution("p_x", self.p_x, self.inputs)  # type: ignore[arg-type]
        _check_distribution("p_noise", self.p_noise, self.labels)
        zero_noise = [label for label in self.labels if self.p_noise[label] <= 0.0]
        if zero_noise:
            raise ValueError(f"p_noise must be positive for every label: {zero_noise}")
        for x_value in self.inputs:
            if x_value not in self.p_y_given_x:
                raise ValueError(f"p_y_given_x is missing input {x_value}")
            _check_distribution(f"p_y_given_x[{x_value}]", self.p_y_given_x[x_value], self.labels)

    def joint_probability(self, x_value: str, y_value: str) -> float:
        return float(self.p_x[x_value]) * float(self.p_y_given_x[x_value][y_value])  # type: ignore[index]

    def bar_score(self, raw_score: float, label: str) -> float:
        return float(raw_score) - math.log(float(self.p_noise[label]))

    def candidate_event_probability(self, x_value: str, positive: str, negatives: Tuple[str, ...]) -> float:
        probability = self.joint_probability(x_value, positive)
        for label in negatives:
            probability *= float(self.p_noise[label])
        return probability

    def enumerate_population_events(self) -> List[dict]:
        events: List[dict] = []
        for x_value in self.inputs:
            for positive in self.labels:
                for negatives in product(self.labels, repeat=self.k_negatives):
                    probability = self.candidate_event_probability(x_value, positive, tuple(negatives))
                    events.append(
                        {
                            "x": x_value,
                            "positive": positive,
                            "negatives": list(negatives),
                            "probability": probability,
                        }
                    )
        return events

    def conditional_ratio(self, x_value: str, numerator: str, denominator: str) -> float:
        return float(self.p_y_given_x[x_value][numerator]) / float(self.p_y_given_x[x_value][denominator])

    def as_jsonable(self) -> dict:
        return {
            "inputs": list(self.inputs),
            "labels": list(self.labels),
            "p_x": dict(self.p_x),  # type: ignore[arg-type]
            "p_y_given_x": {key: dict(value) for key, value in self.p_y_given_x.items()},
            "p_noise": dict(self.p_noise),
            "k_negatives": self.k_negatives,
        }


def section_4_3_score(log_theta1: float, log_theta2: float, x_value: str, y_value: str) -> float:
    if x_value == "x1" and y_value == "y1":
        return log_theta1
    return log_theta2


def section_4_3_partitions(theta1: float = 1.0, theta2: float = 3.0) -> dict:
    return {
        "x1": theta1 + theta2,
        "x2": theta2 + theta2,
    }


def build_section_4_3_protocol(k_negatives: int = 1) -> ConditionalNCEProtocol:
    theta1 = 1.0
    theta2 = 3.0
    z = section_4_3_partitions(theta1, theta2)
    return ConditionalNCEProtocol(
        inputs=("x1", "x2"),
        labels=("y1", "y2"),
        p_x={"x1": 0.5, "x2": 0.5},
        p_y_given_x={
            "x1": {"y1": theta1 / z["x1"], "y2": theta2 / z["x1"]},
            "x2": {"y1": theta2 / z["x2"], "y2": theta2 / z["x2"]},
        },
        p_noise={"y1": 0.5, "y2": 0.5},
        k_negatives=k_negatives,
    )


def normalized_conditionals(
    protocol: ConditionalNCEProtocol,
    score_fn: Callable[[str, str], float],
) -> NestedProbabilityTable:
    result: NestedProbabilityTable = {}
    for x_value in protocol.inputs:
        exp_scores = {label: math.exp(score_fn(x_value, label)) for label in protocol.labels}
        total = sum(exp_scores.values())
        result[x_value] = {label: value / total for label, value in exp_scores.items()}
    return result


def write_protocol_summary(path: str | Path, protocol: ConditionalNCEProtocol) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = protocol.as_jsonable()
    payload["true_ratios"] = {
        "x1_y1_over_y2": protocol.conditional_ratio("x1", "y1", "y2"),
        "x2_y1_over_y2": protocol.conditional_ratio("x2", "y1", "y2"),
    }
    payload["partitions_at_true_theta"] = section_4_3_partitions()
    payload["population_event_mass"] = sum(item["probability"] for item in protocol.enumerate_population_events())
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Write a Section 4.3 conditional NCE protocol summary.")
    parser.add_argument("--k", type=int, default=1, help="Number of negative labels per positive.")
    parser.add_argument("--output", required=True, help="JSON output path.")
    args = parser.parse_args()

    write_protocol_summary(args.output, build_section_4_3_protocol(args.k))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
