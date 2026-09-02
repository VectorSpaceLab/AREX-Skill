#!/usr/bin/env python3
"""EWC penalty and gradient helpers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _validate(theta: list[float], theta_star: list[float], fisher: list[float]) -> None:
    if not (len(theta) == len(theta_star) == len(fisher)):
        raise ValueError("theta, theta_star, and fisher must have identical dimensions")
    if any(value < 0 for value in fisher):
        raise ValueError("fisher entries must be nonnegative")


def ewc_penalty(theta: list[float], theta_star: list[float], fisher: list[float], lambda_value: float) -> float:
    _validate(theta, theta_star, fisher)
    return 0.5 * float(lambda_value) * sum(f * (t - s) ** 2 for t, s, f in zip(theta, theta_star, fisher))


def ewc_gradient(theta: list[float], theta_star: list[float], fisher: list[float], lambda_value: float) -> list[float]:
    _validate(theta, theta_star, fisher)
    return [float(lambda_value) * f * (t - s) for t, s, f in zip(theta, theta_star, fisher)]


def summed_penalty(theta: list[float], anchors: list[dict]) -> float:
    total = 0.0
    for anchor in anchors:
        total += ewc_penalty(theta, anchor["theta_star"], anchor["fisher"], anchor["lambda_value"])
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON with theta, theta_star, fisher, lambda_value")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = {
        "schema_version": 1,
        "penalty": ewc_penalty(data["theta"], data["theta_star"], data["fisher"], data["lambda_value"]),
        "gradient": ewc_gradient(data["theta"], data["theta_star"], data["fisher"], data["lambda_value"]),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
