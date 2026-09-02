#!/usr/bin/env python3
"""Compute NTK trace-ratio loss weights for PINN components."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def compute_weights(trace_full: float, trace_kuu: float, trace_krr: float, epsilon: float = 1e-12) -> dict:
    values = {"trace_full": trace_full, "trace_kuu": trace_kuu, "trace_krr": trace_krr}
    for name, value in values.items():
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"{name} must be a finite nonnegative number")
    if trace_kuu <= epsilon:
        raise ValueError("trace_kuu is degenerate")
    if trace_krr <= epsilon:
        raise ValueError("trace_krr is degenerate")
    lambda_b = trace_full / trace_kuu
    lambda_r = trace_full / trace_krr
    if lambda_b > lambda_r:
        stronger = "boundary"
    elif lambda_r > lambda_b:
        stronger = "residual"
    else:
        stronger = "equal"
    return {
        "schema_version": 1,
        "lambda_b": lambda_b,
        "lambda_r": lambda_r,
        "stronger_weight": stronger,
        "formula": "lambda_component = Tr(K) / Tr(K_component)",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON spectrum diagnostics")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = compute_weights(data["trace_full"], data["trace_kuu"], data["trace_krr"])
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "lambda_b": result["lambda_b"], "lambda_r": result["lambda_r"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
