#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def normalize_approximate(payload: Any) -> dict[str, list[float]]:
    if isinstance(payload, dict) and all(isinstance(value, list) for value in payload.values()):
        return {str(key): [float(item) for item in value] for key, value in payload.items()}
    if isinstance(payload, dict) and all(isinstance(value, (int, float)) for value in payload.values()):
        return {str(key): [float(value)] for key, value in payload.items()}
    if isinstance(payload, list):
        grouped: dict[str, list[float]] = {}
        for row in payload:
            if not isinstance(row, dict):
                continue
            for key, value in row.items():
                if isinstance(value, (int, float)):
                    grouped.setdefault(str(key), []).append(float(value))
        return grouped
    return {}


def compute_accuracy(approximate: Any, reference_means: dict[str, float], reference_squared: dict[str, float] | None = None) -> dict[str, Any]:
    approx = normalize_approximate(approximate)
    approx_means = {name: _mean(values) for name, values in approx.items() if values}
    shared = sorted(set(approx_means) & set(reference_means))
    if not shared:
        raise ValueError("no overlapping approximate and reference parameters")
    per_parameter = {}
    squared_errors = []
    for name in shared:
        error = approx_means[name] - float(reference_means[name])
        squared_errors.append(error * error)
        per_parameter[name] = {"approx_mean": approx_means[name], "reference_mean": float(reference_means[name]), "error": error}
    result: dict[str, Any] = {
        "mean_rmse": math.sqrt(sum(squared_errors) / len(squared_errors)),
        "overlap": shared,
        "missing_approximate": sorted(set(reference_means) - set(approx_means)),
        "extra_approximate": sorted(set(approx_means) - set(reference_means)),
        "per_parameter": per_parameter,
    }
    if reference_squared:
        sq_shared = sorted(set(approx) & set(reference_squared))
        if sq_shared:
            sq_errors = []
            for name in sq_shared:
                approx_squared = _mean([value * value for value in approx[name]])
                sq_errors.append((approx_squared - float(reference_squared[name])) ** 2)
            result["squared_moment_rmse"] = math.sqrt(sum(sq_errors) / len(sq_errors))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--approx", required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--squared-reference", default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    approximate = json.loads(Path(args.approx).read_text(encoding="utf-8"))
    reference = json.loads(Path(args.reference).read_text(encoding="utf-8"))
    squared = json.loads(Path(args.squared_reference).read_text(encoding="utf-8")) if args.squared_reference else None
    result = compute_accuracy(approximate, reference, squared)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
