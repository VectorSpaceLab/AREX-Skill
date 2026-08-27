#!/usr/bin/env python3
"""Tiny PyMC inference/predictive smoke helper."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import warnings
from typing import Any


def has_group(datatree: Any, group: str) -> bool:
    return group in getattr(datatree, "children", {})


def sizes(group: Any) -> dict[str, int]:
    return {str(key): int(value) for key, value in getattr(group, "sizes", {}).items()}


def missing_dep(sampler: str) -> str | None:
    if sampler == "pymc":
        return None
    modules = ["nutpie"] if sampler == "nutpie" else ["jax", "jaxlib", sampler]
    missing = [module for module in modules if importlib.util.find_spec(module) is None]
    return ", ".join(missing) if missing else None


def run(args: argparse.Namespace) -> dict[str, Any]:
    missing = missing_dep(args.nuts_sampler)
    if missing:
        raise RuntimeError(f"Requested {args.nuts_sampler} but missing: {missing}")
    import numpy as np
    import pymc as pm

    with pm.Model(coords={"obs_id": np.arange(6)}) as model:
        x = pm.Data("x", np.linspace(-1, 1, 6), dims="obs_id")
        alpha = pm.Normal("alpha", 0, 1)
        beta = pm.Normal("beta", 0, 1)
        mu = pm.Deterministic("mu", alpha + beta * x, dims="obs_id")
        pm.Normal("y", mu=mu, sigma=0.5, observed=[-0.8, -0.35, -0.1, 0.25, 0.45, 0.9], dims="obs_id")
        prior = pm.sample_prior_predictive(draws=args.prior_draws, random_seed=args.seed, return_inferencedata=True)
        kwargs = dict(
            draws=args.draws,
            tune=args.tune,
            chains=args.chains,
            cores=args.cores,
            random_seed=args.seed + 1,
            progressbar=False,
            quiet=True,
            compute_convergence_checks=args.compute_convergence_checks,
            nuts_sampler=args.nuts_sampler,
            return_inferencedata=True,
        )
        if args.nuts_sampler == "pymc":
            kwargs["nuts"] = {"target_accept": 0.9}
        elif args.nuts_sampler in {"numpyro", "blackjax"}:
            kwargs["nuts"] = {"target_accept": 0.9, "postprocessing_backend": "cpu"}
        else:
            kwargs["nuts"] = {"target_accept": 0.9}
        idata = pm.sample(**kwargs)
        posterior_predictive = pm.sample_posterior_predictive(idata, var_names=["y"], random_seed=args.seed + 2, progressbar=False, return_inferencedata=True)
        idata.update(posterior_predictive)
        pm.compute_log_likelihood(idata, progressbar=False)
        prediction_sizes = None
        if not args.skip_predictions:
            pm.set_data({"x": np.array([-0.5, 0.5])}, coords={"obs_id": np.array([10, 11])})
            predictions = pm.sample_posterior_predictive(idata, var_names=["y"], predictions=True, random_seed=args.seed + 3, progressbar=False, return_inferencedata=True)
            assert has_group(predictions, "predictions")
            prediction_sizes = sizes(predictions.predictions)
        drawn = pm.draw(pm.Normal.dist(0, 1), draws=3, random_seed=args.seed + 4)

    for group in {"prior", "prior_predictive", "observed_data", "constant_data"}:
        assert has_group(prior, group), group
    for group in {"posterior", "sample_stats", "posterior_predictive", "log_likelihood"}:
        assert has_group(idata, group), group
    return {
        "status": "ok",
        "pymc_version": pm.__version__,
        "nuts_sampler": args.nuts_sampler,
        "posterior_groups": sorted(str(key) for key in idata.children),
        "posterior_sizes": sizes(idata.posterior),
        "posterior_predictive_sizes": sizes(idata.posterior_predictive),
        "prediction_sizes": prediction_sizes,
        "draw_shape": list(getattr(drawn, "shape", ())),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a tiny PyMC posterior/prior/posterior-predictive smoke test and assert DataTree groups.")
    parser.add_argument("--nuts-sampler", choices=["pymc", "nutpie", "numpyro", "blackjax"], default="pymc")
    parser.add_argument("--draws", type=int, default=10)
    parser.add_argument("--tune", type=int, default=10)
    parser.add_argument("--chains", type=int, default=1)
    parser.add_argument("--cores", type=int, default=1)
    parser.add_argument("--prior-draws", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20260812)
    parser.add_argument("--compute-convergence-checks", action="store_true")
    parser.add_argument("--skip-predictions", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("default")
            result = run(args)
    except Exception as exc:
        msg = {"status": "error", "error_type": type(exc).__name__, "error": str(exc)}
        print(json.dumps(msg, indent=2) if args.json else f"ERROR: {msg['error_type']}: {msg['error']}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else "PyMC inference smoke: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
