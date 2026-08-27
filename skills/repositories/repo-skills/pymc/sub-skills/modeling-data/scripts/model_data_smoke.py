#!/usr/bin/env python3
"""Tiny PyMC model/data smoke checks."""
from __future__ import annotations

import argparse
import json
import math
import warnings
from typing import Any


def group(obj: Any, name: str) -> Any:
    if hasattr(obj, name):
        return getattr(obj, name)
    return obj[name]


def build(seed: int):
    import numpy as np
    import pymc as pm

    rng = np.random.default_rng(seed)
    with pm.Model(coords={"obs_id": ["a", "b", "c"], "feature": ["f0", "f1"]}) as model:
        x = pm.Data("x", rng.normal(size=(3, 2)), dims=("obs_id", "feature"))
        beta = pm.Normal("beta", 0, 1, dims="feature")
        sigma = pm.HalfNormal("sigma", 1)
        mu = pm.Deterministic("mu", x @ beta, dims="obs_id")
        pm.Potential("sigma_positive_check", pm.math.log(pm.math.switch(sigma > 0, 1, 0)))
        pm.Normal("obs", mu=mu, sigma=sigma, observed=[0.1, -0.2, 0.3], dims="obs_id")
    return model


def core(seed: int) -> dict[str, Any]:
    import numpy as np
    import pymc as pm

    model = build(seed)
    point = model.initial_point(random_seed=seed)
    logp = float(model.compile_logp()(point))
    assert math.isfinite(logp)
    expr = model.replace_rvs_by_values([model["mu"]])[0]
    fn = model.compile_fn(expr, inputs=model.value_vars, on_unused_input="ignore")
    assert np.asarray(fn(point)).shape == (3,)
    with model:
        pm.set_data({"x": np.zeros((2, 2))}, coords={"obs_id": ["new-a", "new-b"]})
    return {"initial_logp": logp, "resized_x_shape": list(model["x"].get_value().shape), "resized_obs_coords": list(model.coords["obs_id"])}


def do_observe() -> dict[str, Any]:
    import numpy as np
    import pymc as pm

    with pm.Model() as model:
        x = pm.Normal("x", 0, 1e-3)
        y = pm.Normal("y", x, 1e-3)
        pm.Normal("z", y + x, 1e-3)
    observed = pm.observe(model, {"y": np.array(0.5)})
    assert [rv.name for rv in observed.observed_RVs] == ["y"]
    obs_logp = float(observed.compile_logp()({"x": 0.1, "z": 0.6}))
    assert math.isfinite(obs_logp)
    intervened = pm.do(model, {"y": np.array(100.0)})
    assert "y" in intervened.named_vars and "y" not in {rv.name for rv in intervened.free_RVs}
    return {"observe_free_RVs": sorted(rv.name for rv in observed.free_RVs), "do_free_RVs": sorted(rv.name for rv in intervened.free_RVs)}


def posterior_prediction(seed: int, draws: int, tune: int) -> dict[str, Any]:
    import numpy as np
    import pymc as pm

    with pm.Model(coords={"obs_id": ["old-a", "old-b", "old-c"]}) as model:
        x = pm.Data("x", np.array([1.0, 2.0, 3.0]), dims="obs_id")
        beta = pm.Normal("beta", 0, 2)
        pm.Normal("obs", mu=beta * x, sigma=0.25, observed=[1.0, 2.0, 3.0], dims="obs_id")
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="The number of samples is too small.*")
            idata = pm.sample(
                draws=draws,
                tune=tune,
                chains=1,
                cores=1,
                random_seed=seed,
                progressbar=False,
                compute_convergence_checks=False,
                nuts_sampler="pymc",
            )
        pm.set_data({"x": np.array([5.0, 6.0])}, coords={"obs_id": ["new-a", "new-b"]})
        out = pm.sample_posterior_predictive(idata, predictions=True, extend_inferencedata=True, random_seed=seed + 1, progressbar=False)
    target = idata if hasattr(idata, "predictions") else out
    predictions = group(target, "predictions")
    assert predictions["obs"].shape[-1] == 2
    return {"prediction_shape": list(predictions["obs"].shape), "prediction_obs_id": [str(v) for v in predictions["obs"].coords["obs_id"].values]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run tiny PyMC model/data checks for Model, Data, set_data, do, observe, and optional posterior prediction resizing.")
    parser.add_argument("--seed", type=int, default=202503)
    parser.add_argument("--posterior-predictive", action="store_true")
    parser.add_argument("--draws", type=int, default=20)
    parser.add_argument("--tune", type=int, default=20)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    import pymc as pm

    result = {"pymc_version": pm.__version__, "core_model": core(args.seed), "do_observe": do_observe()}
    result["posterior_predictive"] = posterior_prediction(args.seed + 20, args.draws, args.tune) if args.posterior_predictive else "skipped"
    if not args.quiet:
        print("PyMC model/data smoke checks passed.")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
