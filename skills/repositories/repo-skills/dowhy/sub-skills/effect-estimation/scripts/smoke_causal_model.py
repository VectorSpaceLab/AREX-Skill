#!/usr/bin/env python3
"""Self-contained synthetic DoWhy CausalModel four-step smoke workflow.

The script generates a small no-download observational dataset with one observed
common cause, identifies a backdoor estimand, estimates it with
``backdoor.linear_regression``, checks the estimate against the known synthetic
ATE, and prints a JSON summary. It imports DoWhy only after argument parsing and
can be run from any working directory when DoWhy is importable in the active
Python environment.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

ESTIMATOR_METHOD = "backdoor.linear_regression"
TRUE_EFFECT = 2.0


def _min_samples(value: str) -> int:
    parsed = int(value)
    if parsed < 50:
        raise argparse.ArgumentTypeError("must be at least 50 for a stable smoke estimate")
    return parsed


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a synthetic DoWhy CausalModel four-step smoke check.")
    parser.add_argument("--samples", type=_min_samples, default=500, help="Synthetic rows to generate. Default: 500.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for data and refuters. Default: 7.")
    parser.add_argument(
        "--tolerance",
        type=_positive_float,
        default=0.25,
        help="Allowed absolute error from the synthetic true effect 2.0. Default: 0.25.",
    )
    parser.add_argument(
        "--run-refuter",
        action="store_true",
        help="Also run random_common_cause with num_simulations=3, random_state=seed, n_jobs=1.",
    )
    parser.add_argument(
        "--run-do",
        action="store_true",
        help="Also call CausalModel.do(1, estimand, method_name='backdoor.linear_regression').",
    )
    return parser


def _import_dependencies() -> tuple[Any, Any, Any]:
    try:
        import numpy as np
        import pandas as pd
        from dowhy import CausalModel
    except ImportError as exc:
        print(
            "ImportError: could not import DoWhy and its scientific Python dependencies. "
            "Install DoWhy in the active environment, for example `python -m pip install dowhy` "
            "or, from a source checkout, `python -m pip install -e .`. "
            f"Original error: {exc}",
            file=sys.stderr,
        )
        raise
    return np, pd, CausalModel


def _make_data(np: Any, pd: Any, samples: int, seed: int) -> Any:
    rng = np.random.default_rng(seed)
    w = rng.normal(loc=0.0, scale=1.0, size=samples)
    propensity = 1.0 / (1.0 + np.exp(-(-0.15 + 0.9 * w)))
    treatment = rng.binomial(1, propensity, size=samples)
    noise = rng.normal(loc=0.0, scale=0.45, size=samples)
    outcome = TRUE_EFFECT * treatment + 1.4 * w + noise
    return pd.DataFrame({"W": w, "T": treatment, "Y": outcome})


def _as_float(np: Any, value: Any) -> float:
    return float(np.asarray(value, dtype=float).mean())


def _first_lines(value: Any, limit: int = 8) -> list[str]:
    lines = [line.strip() for line in str(value).splitlines() if line.strip()]
    return lines[:limit]


def _run(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    np, pd, CausalModel = _import_dependencies()

    data = _make_data(np, pd, args.samples, args.seed)
    model = CausalModel(data=data, treatment="T", outcome="Y", common_causes=["W"])
    estimand = model.identify_effect(proceed_when_unidentifiable=True)
    estimate = model.estimate_effect(
        estimand,
        method_name=ESTIMATOR_METHOD,
        control_value=0,
        treatment_value=1,
        target_units="ate",
    )

    estimated_effect = _as_float(np, estimate.value)
    absolute_error = abs(estimated_effect - TRUE_EFFECT)
    passed = absolute_error <= args.tolerance
    summary: dict[str, Any] = {
        "status": "passed" if passed else "failed",
        "samples": args.samples,
        "seed": args.seed,
        "method_name": ESTIMATOR_METHOD,
        "common_causes": ["W"],
        "true_effect": TRUE_EFFECT,
        "estimated_effect": estimated_effect,
        "absolute_error": absolute_error,
        "tolerance": args.tolerance,
    }

    if args.run_refuter:
        refutation = model.refute_estimate(
            estimand,
            estimate,
            method_name="random_common_cause",
            show_progress_bar=False,
            num_simulations=3,
            random_state=args.seed,
            n_jobs=1,
        )
        summary["refuter"] = {
            "method_name": "random_common_cause",
            "num_simulations": 3,
            "random_state": args.seed,
            "n_jobs": 1,
            "text_first_lines": _first_lines(refutation),
        }

    if args.run_do:
        do_value = model.do(1, estimand, method_name=ESTIMATOR_METHOD)
        summary["do"] = {
            "x": 1,
            "method_name": ESTIMATOR_METHOD,
            "mean_outcome": _as_float(np, do_value),
        }

    return (0 if passed else 1), summary


def main() -> int:
    args = _make_parser().parse_args()
    try:
        exit_code, summary = _run(args)
    except ImportError:
        return 2
    except Exception as exc:  # noqa: BLE001 - script should report actionable JSON for smoke failures.
        summary = {"status": "failed", "error_type": type(exc).__name__, "error": str(exc)}
        print(f"Error: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 1

    print(json.dumps(summary, indent=2, sort_keys=True))
    if exit_code != 0:
        print(
            "Estimate check failed: increase --samples, inspect the environment, or relax --tolerance only if justified.",
            file=sys.stderr,
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
