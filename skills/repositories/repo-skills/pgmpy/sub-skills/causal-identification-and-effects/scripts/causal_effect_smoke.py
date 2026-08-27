#!/usr/bin/env python3
"""Smoke-test pgmpy's causal identification and effect APIs.

This helper imports an installed pgmpy package, builds tiny deterministic
fixtures, identifies an adjustment set, validates a frontdoor set, estimates an
ATE, and fits a sklearn-style causal regressor. It does not read repository
files, download data, or require optional torch/pyro, plotting, or LLM extras.

Example:
    python causal_effect_smoke.py
    python causal_effect_smoke.py --samples 50 --skip-ate
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from dataclasses import dataclass


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def _nonnegative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


@dataclass
class SmokeResult:
    adjustment_success: bool
    adjustment_set: list[str]
    adjustment_valid: bool
    frontdoor_success: bool
    frontdoor_set: list[str]
    regressor_effect: float
    ate: float | None
    samples: int
    tolerance: float

    def as_dict(self) -> dict[str, object]:
        return {
            "adjustment_success": self.adjustment_success,
            "adjustment_set": self.adjustment_set,
            "adjustment_valid": self.adjustment_valid,
            "frontdoor_success": self.frontdoor_success,
            "frontdoor_set": self.frontdoor_set,
            "regressor_effect": self.regressor_effect,
            "ate": self.ate,
            "samples": self.samples,
            "tolerance": self.tolerance,
        }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a deterministic pgmpy causal identification/effect smoke test.",
    )
    parser.add_argument(
        "--samples",
        type=_positive_int,
        default=80,
        help="Number of synthetic rows to generate for the numeric effect fixture (default: 80).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=7,
        help="Random seed for the deterministic fixture (default: 7).",
    )
    parser.add_argument(
        "--effect",
        type=float,
        default=2.0,
        help="True X -> Y effect used in the fixture (default: 2.0).",
    )
    parser.add_argument(
        "--tolerance",
        type=_nonnegative_float,
        default=1e-8,
        help="Absolute tolerance for deterministic coefficient/ATE checks (default: 1e-8).",
    )
    parser.add_argument(
        "--skip-ate",
        action="store_true",
        help="Skip CausalInference.estimate_ate and only run identification plus regressor checks.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON summary instead of a human-readable summary.",
    )
    return parser


def run_smoke(samples: int, seed: int, effect: float, tolerance: float, skip_ate: bool) -> SmokeResult:
    try:
        import numpy as np
        import pandas as pd
        from pgmpy.base import DAG
        from pgmpy.identification import Adjustment, Frontdoor
        from pgmpy.inference import CausalInference
        from pgmpy.prediction import NaiveAdjustmentRegressor
    except ImportError as exc:  # pragma: no cover - exercised only in broken environments.
        raise RuntimeError(
            "Could not import pgmpy with its base dependencies. Install pgmpy before running this smoke test."
        ) from exc

    if samples < 20:
        raise ValueError("Use at least 20 samples so sklearn validation has a stable 2D fixture.")

    rng = np.random.default_rng(seed)
    z = rng.normal(size=samples)
    x = 0.6 * z + rng.normal(size=samples)
    y = effect * x + 0.3 * z
    data = pd.DataFrame({"X": x, "Z": z, "Y": y})

    graph = DAG(
        [("Z", "X"), ("Z", "Y"), ("X", "Y")],
        roles={"exposures": "X", "outcomes": "Y"},
    )
    identified_graph, adjustment_success = Adjustment(variant="minimal").identify(graph)
    adjustment_set = identified_graph.get_role("adjustment")
    adjustment_valid = Adjustment(variant="minimal").validate(identified_graph)

    if not adjustment_success or adjustment_set != ["Z"] or not adjustment_valid:
        raise AssertionError(
            f"Expected adjustment ['Z']; got success={adjustment_success}, "
            f"adjustment={adjustment_set}, valid={adjustment_valid}."
        )

    frontdoor_graph = DAG(
        [("X", "M"), ("M", "Y"), ("U", "X"), ("U", "Y")],
        latents={"U"},
        roles={"exposures": "X", "outcomes": "Y"},
    )
    identified_frontdoor, frontdoor_success = Frontdoor().identify(frontdoor_graph)
    frontdoor_set = identified_frontdoor.get_role("frontdoor")
    if not frontdoor_success or frontdoor_set != ["M"] or not Frontdoor().validate(identified_frontdoor):
        raise AssertionError(
            f"Expected frontdoor ['M']; got success={frontdoor_success}, frontdoor={frontdoor_set}."
        )

    required_columns = ["X", *adjustment_set]
    missing = sorted(set(required_columns) - set(data.columns))
    if missing:
        raise AssertionError(f"Fixture is missing required columns: {missing}")

    regressor = NaiveAdjustmentRegressor(causal_graph=identified_graph)
    regressor.fit(data[required_columns], data["Y"])
    regressor_effect = float(regressor.estimator_.coef_[0])
    if abs(regressor_effect - effect) > tolerance:
        raise AssertionError(
            f"Expected regressor effect {effect}, got {regressor_effect}; tolerance={tolerance}."
        )

    ate = None
    if not skip_ate:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            ate = float(
                CausalInference(graph).estimate_ate(
                    "X",
                    "Y",
                    data=data,
                    estimand_strategy="smallest",
                    estimator_type="linear",
                )
            )
        if abs(ate - effect) > tolerance:
            raise AssertionError(f"Expected ATE {effect}, got {ate}; tolerance={tolerance}.")

    return SmokeResult(
        adjustment_success=adjustment_success,
        adjustment_set=adjustment_set,
        adjustment_valid=adjustment_valid,
        frontdoor_success=frontdoor_success,
        frontdoor_set=frontdoor_set,
        regressor_effect=regressor_effect,
        ate=ate,
        samples=samples,
        tolerance=tolerance,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    try:
        result = run_smoke(
            samples=args.samples,
            seed=args.seed,
            effect=args.effect,
            tolerance=args.tolerance,
            skip_ate=args.skip_ate,
        )
    except Exception as exc:
        print(f"causal_effect_smoke: FAILED: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result.as_dict(), sort_keys=True))
    else:
        print("causal_effect_smoke: ok")
        print(f"  adjustment: success={result.adjustment_success}, set={result.adjustment_set}")
        print(f"  frontdoor: success={result.frontdoor_success}, set={result.frontdoor_set}")
        print(f"  regressor_effect: {result.regressor_effect:.12g}")
        if result.ate is not None:
            print(f"  ate: {result.ate:.12g}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
