#!/usr/bin/env python3
"""Run a tiny end-to-end PyMC model, sampling, prediction, and intervention smoke."""
from __future__ import annotations

import argparse
import json
import math
import warnings
from typing import Any


def sizes(group: Any) -> dict[str, int]:
    return {str(key): int(value) for key, value in getattr(group, "sizes", {}).items()}


def run(seed: int, draws: int, tune: int, chains: int) -> dict[str, Any]:
    import numpy as np
    import pymc as pm

    rng = np.random.default_rng(seed)
    x_data = rng.normal(size=(8, 2))
    beta_true = np.array([1.5, -0.75])
    y_data = x_data @ beta_true + rng.normal(scale=0.1, size=8)

    with pm.Model(coords={"obs": np.arange(8), "feature": ["f0", "f1"]}) as model:
        x = pm.Data("x", x_data, dims=("obs", "feature"))
        beta = pm.Normal("beta", 0, 2, dims="feature")
        sigma = pm.HalfNormal("sigma", 1)
        mu = pm.Deterministic("mu", x @ beta, dims="obs")
        pm.Normal("y", mu=mu, sigma=sigma, observed=y_data, dims="obs")

        point = model.initial_point(random_seed=seed)
        logp = float(model.compile_logp()(point))
        assert math.isfinite(logp)

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="The number of samples is too small.*")
            idata = pm.sample(
                draws=draws,
                tune=tune,
                chains=chains,
                cores=1,
                random_seed=seed,
                progressbar=False,
                compute_convergence_checks=False,
                nuts_sampler="pymc",
            )
        pm.set_data({"x": rng.normal(size=(3, 2))}, coords={"obs": ["new-a", "new-b", "new-c"]})
        pred = pm.sample_posterior_predictive(
            idata,
            var_names=["y"],
            predictions=True,
            random_seed=seed + 1,
            progressbar=False,
            return_inferencedata=True,
        )

    intervened = pm.do(model, {model["beta"]: np.array([0.0, beta_true[1]])})
    assert "beta" in intervened.named_vars
    if sizes(pred.predictions).get("obs") != 3:
        raise AssertionError(sizes(pred.predictions))
    return {
        "pymc_version": pm.__version__,
        "initial_logp": logp,
        "posterior_sizes": sizes(idata.posterior),
        "prediction_sizes": sizes(pred.predictions),
        "prediction_obs_coord": [str(v) for v in pred.predictions["y"].coords["obs"].values],
        "intervened_model_variables": sorted(intervened.named_vars),
        "note": "tiny smoke only; increase draws/tune/chains for inference quality",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a tiny CPU-only PyMC linear-model smoke with sampling, predictions, and pm.do intervention.")
    parser.add_argument("--seed", type=int, default=20260812)
    parser.add_argument("--draws", type=int, default=20)
    parser.add_argument("--tune", type=int, default=20)
    parser.add_argument("--chains", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = run(args.seed, args.draws, args.tune, args.chains)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("PyMC quick smoke: OK")
        print("  posterior sizes:", result["posterior_sizes"])
        print("  prediction sizes:", result["prediction_sizes"])
        print("  note:", result["note"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
