#!/usr/bin/env python3
"""Scalar composition for the RAIL-KD total training objective."""
from __future__ import annotations

import argparse
import json
import math
from typing import Dict, Sequence, Tuple


def validate_losses(ce_loss: float, kd_loss: float, rail_loss: float) -> None:
    for name, value in [("ce_loss", ce_loss), ("kd_loss", kd_loss), ("rail_loss", rail_loss)]:
        if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError(f"{name} must be a finite scalar")
        if float(value) < 0.0:
            raise ValueError(f"{name} must be non-negative")


def validate_lambdas(lambdas: Sequence[float], tol: float = 1e-8) -> Tuple[float, float, float]:
    if len(lambdas) != 3:
        raise ValueError("exactly three lambda weights are required")
    vals = tuple(float(x) for x in lambdas)
    if any((not math.isfinite(x)) or x < 0.0 for x in vals):
        raise ValueError("lambda weights must be finite and non-negative")
    if abs(sum(vals) - 1.0) > tol:
        raise ValueError("lambda weights must sum to one")
    return vals  # type: ignore[return-value]


def total_objective(ce_loss: float, kd_loss: float, rail_loss: float, lambdas: Sequence[float]) -> Dict[str, object]:
    validate_losses(ce_loss, kd_loss, rail_loss)
    l1, l2, l3 = validate_lambdas(lambdas)
    contributions = {
        "ce": l1 * ce_loss,
        "kd": l2 * kd_loss,
        "rail": l3 * rail_loss,
    }
    total = sum(contributions.values())
    return {
        "total_loss": total,
        "components": {"ce_loss": ce_loss, "kd_loss": kd_loss, "rail_loss": rail_loss},
        "lambdas": {"lambda1": l1, "lambda2": l2, "lambda3": l3},
        "contributions": contributions,
        "weights_sum_to_one": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ce", type=float, required=True)
    parser.add_argument("--kd", type=float, required=True)
    parser.add_argument("--rail", type=float, required=True)
    parser.add_argument("--lambdas", type=float, nargs=3, required=True)
    args = parser.parse_args()
    print(json.dumps(total_objective(args.ce, args.kd, args.rail, args.lambdas), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
