#!/usr/bin/env python3
"""Compute small empirical PINN NTK block diagnostics."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def matmul_left_gram(matrix: list[list[float]]) -> list[list[float]]:
    return [[sum(a * b for a, b in zip(row_i, row_j)) for row_j in matrix] for row_i in matrix]


def trace(matrix: list[list[float]]) -> float:
    return sum(matrix[i][i] for i in range(len(matrix)))


def eigenvalues_symmetric_2_or_diag(matrix: list[list[float]]) -> list[float]:
    if len(matrix) == 1:
        return [matrix[0][0]]
    if len(matrix) == 2:
        a = matrix[0][0]
        b = matrix[0][1]
        c = matrix[1][1]
        center = 0.5 * (a + c)
        radius = math.sqrt(max(0.0, 0.25 * (a - c) * (a - c) + b * b))
        return [center + radius, center - radius]
    return [matrix[i][i] for i in range(len(matrix))]


def validate_jacobians(boundary_jacobian: list[list[float]], residual_jacobian: list[list[float]]) -> None:
    if not boundary_jacobian or not residual_jacobian:
        raise ValueError("jacobians must be non-empty")
    param_dim = len(boundary_jacobian[0])
    if param_dim == 0:
        raise ValueError("jacobian rows must be non-empty")
    for rows in [boundary_jacobian, residual_jacobian]:
        for row in rows:
            if len(row) != param_dim:
                raise ValueError("jacobians must share a parameter dimension")
            if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in row):
                raise ValueError("jacobians must contain finite numbers")


def compute_spectrum(boundary_jacobian: list[list[float]], residual_jacobian: list[list[float]], tolerance: float = 1.5) -> dict:
    validate_jacobians(boundary_jacobian, residual_jacobian)
    kuu = matmul_left_gram(boundary_jacobian)
    krr = matmul_left_gram(residual_jacobian)
    trace_kuu = trace(kuu)
    trace_krr = trace(krr)
    if trace_krr > tolerance * max(trace_kuu, 1e-30):
        dominance = "residual_dominates"
    elif trace_kuu > tolerance * max(trace_krr, 1e-30):
        dominance = "boundary_dominates"
    else:
        dominance = "balanced"
    return {
        "schema_version": 1,
        "trace_kuu": trace_kuu,
        "trace_krr": trace_krr,
        "trace_full": trace_kuu + trace_krr,
        "eigenvalues_kuu": sorted(eigenvalues_symmetric_2_or_diag(kuu), reverse=True),
        "eigenvalues_krr": sorted(eigenvalues_symmetric_2_or_diag(krr), reverse=True),
        "dominance": dominance,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON with boundary_jacobian and residual_jacobian")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = compute_spectrum(data["boundary_jacobian"], data["residual_jacobian"])
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "dominance": result["dominance"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
