#!/usr/bin/env python3
"""Safe template for invoking several DoWhy refuters with parallel knobs.

The script creates a synthetic no-download ``CausalModel`` estimate with one
observed common cause, then runs selected refuters with explicit
``num_simulations``, ``random_state``, and ``n_jobs`` settings when supported by
the refuter. It prints a JSON summary containing the original estimate and the
first lines of each refuter result. DoWhy is imported only after argument
parsing, so ``--help`` works even before the package is installed.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

ESTIMATOR_METHOD = "backdoor.linear_regression"
TRUE_EFFECT = 2.0
REFUTER_CHOICES = (
    "random_common_cause",
    "placebo_treatment_refuter",
    "data_subset_refuter",
    "bootstrap_refuter",
)
DEFAULT_REFUTERS = ["random_common_cause", "data_subset_refuter"]
REFUTERS_ACCEPTING_N_JOBS = set(REFUTER_CHOICES)


def _min_samples(value: str) -> int:
    parsed = int(value)
    if parsed < 50:
        raise argparse.ArgumentTypeError("must be at least 50 for stable refuter smoke runs")
    return parsed


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _n_jobs(value: str) -> int:
    parsed = int(value)
    if parsed == 0 or parsed < -1:
        raise argparse.ArgumentTypeError("must be -1 or a positive integer")
    return parsed


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run synthetic DoWhy refuters with explicit parallel settings.")
    parser.add_argument("--samples", type=_min_samples, default=500, help="Synthetic rows to generate. Default: 500.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for data and refuters. Default: 7.")
    parser.add_argument(
        "--num-simulations",
        type=_positive_int,
        default=3,
        help="Number of simulations for each selected refuter. Default: 3.",
    )
    parser.add_argument(
        "--n-jobs",
        type=_n_jobs,
        default=1,
        help="joblib n_jobs for refuters that accept it; use -1 for all CPUs. Default: 1.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Pass verbose=1 to refuters that accept joblib verbosity. Default: false.",
    )
    parser.add_argument(
        "--refuters",
        nargs="+",
        choices=REFUTER_CHOICES,
        default=DEFAULT_REFUTERS,
        help="One or more refuters to run. Default: random_common_cause data_subset_refuter.",
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


def _refuter_kwargs(name: str, args: argparse.Namespace) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"num_simulations": args.num_simulations, "random_state": args.seed}
    if name in REFUTERS_ACCEPTING_N_JOBS:
        kwargs["n_jobs"] = args.n_jobs
        kwargs["verbose"] = 1 if args.verbose else 0
    if name == "placebo_treatment_refuter":
        kwargs["placebo_type"] = "permute"
    elif name == "data_subset_refuter":
        kwargs["subset_fraction"] = 0.8
    elif name == "bootstrap_refuter":
        kwargs["sample_size"] = args.samples
        kwargs["required_variables"] = True
        kwargs["noise"] = 0.01
    return kwargs


def _strip_parallel_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in kwargs.items() if key not in {"n_jobs", "verbose"}}


def _run_refuter(model: Any, estimand: Any, estimate: Any, name: str, kwargs: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    try:
        return (
            model.refute_estimate(
                estimand,
                estimate,
                method_name=name,
                show_progress_bar=False,
                **kwargs,
            ),
            kwargs,
        )
    except TypeError as exc:
        message = str(exc)
        if "n_jobs" not in message and "verbose" not in message:
            raise
        fallback_kwargs = _strip_parallel_kwargs(kwargs)
        return (
            model.refute_estimate(
                estimand,
                estimate,
                method_name=name,
                show_progress_bar=False,
                **fallback_kwargs,
            ),
            fallback_kwargs,
        )


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
    original_estimate = _as_float(np, estimate.value)

    summary: dict[str, Any] = {
        "status": "passed",
        "samples": args.samples,
        "seed": args.seed,
        "method_name": ESTIMATOR_METHOD,
        "true_effect": TRUE_EFFECT,
        "original_estimate": original_estimate,
        "num_simulations": args.num_simulations,
        "n_jobs_requested": args.n_jobs,
        "refuters": [],
    }

    failed = False
    for name in args.refuters:
        requested_kwargs = _refuter_kwargs(name, args)
        result: dict[str, Any] = {"method_name": name, "requested_kwargs": requested_kwargs}
        try:
            refutation, used_kwargs = _run_refuter(model, estimand, estimate, name, requested_kwargs)
            result.update(
                {
                    "status": "passed",
                    "used_kwargs": used_kwargs,
                    "text_first_lines": _first_lines(refutation),
                }
            )
        except ImportError as exc:
            failed = True
            message = (
                f"ImportError while running {name}: optional dependency or refuter import failed. "
                f"Original error: {exc}"
            )
            print(message, file=sys.stderr)
            result.update({"status": "import_error", "error": message})
        except Exception as exc:  # noqa: BLE001 - continue so all selected refuters are reported.
            failed = True
            message = f"{type(exc).__name__} while running {name}: {exc}"
            print(message, file=sys.stderr)
            result.update({"status": "failed", "error_type": type(exc).__name__, "error": str(exc)})
        summary["refuters"].append(result)

    if failed:
        summary["status"] = "failed"
    return (1 if failed else 0), summary


def main() -> int:
    args = _make_parser().parse_args()
    try:
        exit_code, summary = _run(args)
    except ImportError:
        return 2
    except Exception as exc:  # noqa: BLE001 - script should report actionable JSON for template failures.
        summary = {"status": "failed", "error_type": type(exc).__name__, "error": str(exc)}
        print(f"Error: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 1

    print(json.dumps(summary, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
