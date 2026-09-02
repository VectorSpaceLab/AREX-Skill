#!/usr/bin/env python3
"""Validate tiny simulator/prior records for SBI-style recovery experiments."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Callable, Iterable, Sequence


Number = int | float


def as_float_vector(value: object) -> list[float]:
    """Convert a scalar or flat sequence into a numeric vector."""
    if isinstance(value, bool):
        raise ValueError("boolean values are not valid numeric simulator values")
    if isinstance(value, (int, float)):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("value is not finite")
        return [number]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        vector: list[float] = []
        for item in value:
            if isinstance(item, bool) or not isinstance(item, (int, float)):
                raise ValueError("sequence contains a nonnumeric value")
            number = float(item)
            if not math.isfinite(number):
                raise ValueError("sequence contains a nonfinite value")
            vector.append(number)
        if not vector:
            raise ValueError("empty vectors are not valid simulator values")
        return vector
    raise ValueError(f"unsupported value type: {type(value).__name__}")


def deterministic_prior_grid(count: int, low: float = -2.0, high: float = 2.0) -> list[list[float]]:
    if count <= 0:
        raise ValueError("count must be positive")
    if count == 1:
        return [[(float(low) + float(high)) / 2.0]]
    step = (float(high) - float(low)) / float(count - 1)
    return [[float(low) + step * idx] for idx in range(count)]


def run_protocol(
    theta_values: Iterable[object],
    simulator: Callable[[list[float]], object],
    *,
    expected_x_dim: int | None = None,
    vectorized: bool = False,
) -> dict:
    records: list[dict] = []
    theta_dim: int | None = None
    x_dim: int | None = expected_x_dim
    warnings: list[str] = []

    for idx, theta_raw in enumerate(theta_values):
        try:
            theta = as_float_vector(theta_raw)
            if theta_dim is None:
                theta_dim = len(theta)
            elif len(theta) != theta_dim:
                raise ValueError(f"theta dimension {len(theta)} != expected {theta_dim}")
            x = as_float_vector(simulator(theta))
            if x_dim is None:
                x_dim = len(x)
            elif len(x) != x_dim:
                raise ValueError(f"x dimension {len(x)} != expected {x_dim}")
            record = {"index": idx, "theta": theta, "x": x, "status": "ok"}
        except Exception as exc:
            record = {
                "index": idx,
                "theta": theta_raw if isinstance(theta_raw, list) else theta_raw,
                "x": None,
                "status": "failed",
                "error": str(exc),
            }
        records.append(record)

    valid = [item for item in records if item.get("status") == "ok"]
    failed = [item for item in records if item.get("status") != "ok"]
    if not valid:
        warnings.append("no valid simulator records were produced")
    metadata = {
        "theta_dim": theta_dim or 0,
        "x_dim": x_dim or 0,
        "num_requested": len(records),
        "num_valid": len(valid),
        "num_failed": len(failed),
        "vectorized_assumed": bool(vectorized),
        "warnings": warnings,
    }
    return {"schema_version": 1, "records": records, "valid_records": valid, "metadata": metadata}


def linear_gaussian_style_simulator(theta: list[float], noise: float = 0.0) -> list[float]:
    return [theta[0] + float(noise)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Run a deterministic built-in protocol demo.")
    parser.add_argument("--count", type=int, default=5, help="Number of demo prior samples.")
    parser.add_argument("--output", default="", help="Optional JSON output path.")
    args = parser.parse_args()

    if not args.demo:
        parser.error("only --demo is implemented for the standalone CLI")

    result = run_protocol(deterministic_prior_grid(args.count), linear_gaussian_style_simulator)
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        path = Path(args.output).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
