#!/usr/bin/env python3
"""Run tiny CPU-only smoke checks for PyMC advanced workflows."""
from __future__ import annotations

import argparse
import json
import time
import warnings
from dataclasses import asdict, dataclass
from typing import Callable

import numpy as np


@dataclass
class CheckResult:
    name: str
    status: str
    seconds: float
    detail: str


def time_check(name: str, fn: Callable[[], str]) -> CheckResult:
    start = time.perf_counter()
    try:
        detail = fn()
        return CheckResult(name, "passed", time.perf_counter() - start, detail)
    except Exception as exc:
        return CheckResult(name, "failed", time.perf_counter() - start, repr(exc))


def gp(seed: int) -> str:
    import pymc as pm

    rng = np.random.default_rng(seed)
    X = np.linspace(0, 1, 4)[:, None]
    Xnew = np.linspace(-0.1, 1.1, 3)[:, None]
    y = np.sin(2 * np.pi * X[:, 0]) + 0.01 * rng.normal(size=4)
    cov = pm.gp.cov.ExpQuad(input_dim=1, ls=0.3)
    K = np.asarray(cov(X).eval())
    assert K.shape == (4, 4) and np.isfinite(K).all() and np.allclose(K, K.T)
    with pm.Model() as model:
        latent = pm.gp.Latent(cov_func=cov)
        latent.prior("f", X=X, reparameterize=False)
        latent.conditional("f_new", Xnew=Xnew)
        marginal = pm.gp.Marginal(cov_func=cov)
        marginal.marginal_likelihood("y", X=X, y=y, sigma=0.1)
        logp = model.compile_logp()(model.initial_point())
    assert np.isfinite(logp)
    return "covariance shape=(4, 4); latent conditional and marginal logp constructed"


def ode(seed: int) -> str:
    import pymc as pm
    import pytensor.tensor as pt

    def system(y, t, p):
        return pt.exp(-t) - p[0] * y[0]

    times = np.arange(0.5, 2.5, 0.5)
    ode_model = pm.ode.DifferentialEquation(func=system, times=times, n_states=1, n_theta=1, t0=0.0)
    simulated, sensitivities = ode_model._simulate(y0=[0.0], theta=[0.4])
    assert simulated.shape == (len(times), 1)
    assert sensitivities.shape == (len(times), 1, 2)
    assert np.isfinite(simulated).all()
    with pm.Model() as model:
        alpha = pm.HalfNormal("alpha", sigma=1.0, initval=0.4)
        forward = ode_model(y0=[0.0], theta=[alpha])
        pm.Normal("obs", mu=forward, sigma=0.1, observed=simulated)
        logp = model.compile_logp()(model.initial_point())
    assert np.isfinite(logp)
    return f"states shape={simulated.shape}; sensitivities shape={sensitivities.shape}; finite logp"


def vi(seed: int, iterations: int, draws: int) -> str:
    import pymc as pm

    rng = np.random.default_rng(seed)
    observed = rng.normal(loc=0.5, scale=0.2, size=8)
    with pm.Model() as model:
        mu = pm.Normal("mu", 0, 1)
        sigma = pm.HalfNormal("sigma", 1)
        pm.Normal("y", mu=mu, sigma=sigma, observed=observed)
        assert np.isfinite(model.compile_logp()(model.initial_point()))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            approx = pm.fit(n=iterations, method="advi", random_seed=seed, progressbar=False, obj_optimizer=pm.adam(learning_rate=0.01))
            idata = approx.sample(draws=draws, random_seed=seed + 1)
    assert hasattr(idata, "posterior") and "mu" in idata.posterior
    return f"ADVI iterations={iterations}; approximation posterior mu shape={tuple(idata.posterior['mu'].shape)}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run tiny CPU-only PyMC advanced-workflow smoke checks.")
    parser.add_argument("--gp", action="store_true")
    parser.add_argument("--ode", action="store_true")
    parser.add_argument("--vi", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--vi-iterations", type=int, default=5)
    parser.add_argument("--vi-draws", type=int, default=5)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    run_all = args.all or not (args.gp or args.ode or args.vi)
    selected: list[tuple[str, Callable[[], str]]] = []
    if run_all or args.gp:
        selected.append(("gp", lambda: gp(args.seed)))
    if run_all or args.ode:
        selected.append(("ode", lambda: ode(args.seed)))
    if run_all or args.vi:
        selected.append(("vi", lambda: vi(args.seed, args.vi_iterations, args.vi_draws)))
    results = [time_check(name, fn) for name, fn in selected]
    ok = all(result.status == "passed" for result in results)
    if args.json:
        print(json.dumps({"ok": ok, "results": [asdict(result) for result in results]}, indent=2))
    else:
        print("\n".join(f"[{result.status}] {result.name}: {result.detail}" for result in results))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
