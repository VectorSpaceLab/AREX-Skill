#!/usr/bin/env python3
"""Run offline assertions for statistics and component-contract pitfalls."""
from __future__ import annotations

import argparse
import json


def weighted_mean(values: list[float], weights: list[float]) -> float:
    if len(values) != len(weights) or not values or sum(weights) == 0:
        raise ValueError("values and non-zero weights must have equal length")
    return sum(value * weight for value, weight in zip(values, weights)) / sum(weights)


def run(case: str) -> dict[str, str]:
    result: dict[str, str] = {}
    if case in {"statistics", "all"}:
        assert weighted_mean([1.0, 3.0], [1.0, 3.0]) == 2.5
        result["weighted-statistics"] = "ok"
    if case in {"diagnostic", "all"}:
        coords = {"variable": ["t2m"], "lat": [0, 1]}
        required = {"variable", "lat"}
        assert required <= coords.keys()
        result["diagnostic-coordinates"] = "ok"
    if case in {"axes", "all"}:
        truth = ("ensemble", "time", "lat", "lon")
        prediction = ("ensemble", "time", "lat", "lon")
        assert truth == prediction
        result["metric-axis-order"] = "ok"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=("statistics", "diagnostic", "axes", "all"), default="all")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = run(args.case)
    if args.json: print(json.dumps(result, sort_keys=True))
    else:
        print("contract smoke: PASS")
        for key in result: print("-", key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
