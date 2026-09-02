"""Binary NCE objective and self-normalization diagnostics."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Callable, Dict


PROTOCOL_SCRIPTS = Path(__file__).resolve().parents[2] / "conditional_nce_protocol" / "scripts"
if str(PROTOCOL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PROTOCOL_SCRIPTS))

from conditional_nce_protocol import (  # noqa: E402
    ConditionalNCEProtocol,
    build_section_4_3_protocol,
    normalized_conditionals,
    section_4_3_partitions,
    section_4_3_score,
)


def section_4_3_score_from_params(params: Dict[str, float]) -> Callable[[str, str], float]:
    log_theta1 = float(params["log_theta1"])
    log_theta2 = float(params["log_theta2"])
    return lambda x_value, y_value: section_4_3_score(log_theta1, log_theta2, x_value, y_value)


def binary_posterior_g(protocol: ConditionalNCEProtocol, score_fn: Callable[[str, str], float], offset: float, x_value: str, label: str) -> float:
    adjusted = protocol.bar_score(score_fn(x_value, label), label) - offset
    numerator = math.exp(adjusted)
    return numerator / (numerator + protocol.k_negatives)


def binary_objective(protocol: ConditionalNCEProtocol, score_fn: Callable[[str, str], float], offset: float) -> float:
    total = 0.0
    for x_value in protocol.inputs:
        for label in protocol.labels:
            data_weight = protocol.joint_probability(x_value, label)
            noise_weight = float(protocol.p_x[x_value]) * float(protocol.p_noise[label])
            g_value = binary_posterior_g(protocol, score_fn, offset, x_value, label)
            total += data_weight * math.log(g_value)
            total += protocol.k_negatives * noise_weight * math.log(1.0 - g_value)
    return total


def section_4_3_binary_limit(offset: float = 0.0) -> Dict[str, float]:
    theta1 = 0.25 * math.exp(offset)
    theta2 = (7.0 / 12.0) * math.exp(offset)
    return {
        "theta1": theta1,
        "theta2": theta2,
        "ratio_x1": theta1 / theta2,
        "paper_inconsistent_ratio": 3.0 / 7.0,
        "true_ratio_x1": 1.0 / 3.0,
    }


def self_normalization_report(theta1: float = 1.0, theta2: float = 3.0) -> dict:
    partitions = section_4_3_partitions(theta1, theta2)
    values = list(partitions.values())
    return {
        "partitions": partitions,
        "constant_partition": max(values) - min(values) < 1e-12,
        "partition_range": max(values) - min(values),
    }


def run_binary_diagnostic(k_negatives: int = 2, offset: float = 0.0) -> dict:
    protocol = build_section_4_3_protocol(k_negatives)
    limit = section_4_3_binary_limit(offset)
    params = {"log_theta1": math.log(limit["theta1"]), "log_theta2": math.log(limit["theta2"])}
    score_fn = section_4_3_score_from_params(params)
    conditionals = normalized_conditionals(protocol, score_fn)
    return {
        "objective": binary_objective(protocol, score_fn, offset),
        "offset": offset,
        "analytic_limit": limit,
        "conditionals": conditionals,
        "self_normalization": self_normalization_report(),
        "binary_ratio_error_against_true": abs(limit["ratio_x1"] - limit["true_ratio_x1"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Section 4.3 binary NCE inconsistency diagnostic.")
    parser.add_argument("--k", type=int, default=2)
    parser.add_argument("--offset", type=float, default=0.0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = run_binary_diagnostic(args.k, args.offset)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "ratio_x1": result["analytic_limit"]["ratio_x1"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
