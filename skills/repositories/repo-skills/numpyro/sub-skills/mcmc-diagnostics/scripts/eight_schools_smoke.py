#!/usr/bin/env python3
"""Tiny CPU-safe NumPyro eight-schools MCMC smoke test.

This adapts NumPyro's public eight-schools example for plumbing checks only.
It verifies NUTS, MCMC sample keys/shapes, extra field collection, and optional
posterior predictive output. Tiny defaults are not convergence settings.
"""

from __future__ import annotations

import argparse

from jax import random
import jax.numpy as jnp

import numpyro
import numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS, Predictive
from numpyro.infer.reparam import LocScaleReparam


def centered_eight_schools(J: int, sigma: jnp.ndarray, y: jnp.ndarray | None = None) -> None:
    mu = numpyro.sample("mu", dist.Normal(0.0, 5.0))
    tau = numpyro.sample("tau", dist.HalfCauchy(5.0))
    with numpyro.plate("J", J):
        theta = numpyro.sample("theta", dist.Normal(mu, tau))
        numpyro.sample("obs", dist.Normal(theta, sigma), obs=y)


def noncentered_eight_schools(J: int, sigma: jnp.ndarray, y: jnp.ndarray | None = None) -> None:
    mu = numpyro.sample("mu", dist.Normal(0.0, 5.0))
    tau = numpyro.sample("tau", dist.HalfCauchy(5.0))
    with numpyro.plate("J", J):
        with numpyro.handlers.reparam(config={"theta": LocScaleReparam(centered=0.0)}):
            theta = numpyro.sample("theta", dist.Normal(mu, tau))
        numpyro.sample("obs", dist.Normal(theta, sigma), obs=y)


def new_school() -> None:
    mu = numpyro.sample("mu", dist.Normal(0.0, 5.0))
    tau = numpyro.sample("tau", dist.HalfCauchy(5.0))
    numpyro.sample("obs", dist.Normal(mu, tau))


def run(args: argparse.Namespace) -> None:
    if args.x64:
        numpyro.enable_x64()
    if args.platform:
        numpyro.set_platform(args.platform)

    y = jnp.array([28.0, 8.0, -3.0, 7.0, -1.0, 1.0, 18.0, 12.0])
    sigma = jnp.array([15.0, 10.0, 16.0, 11.0, 9.0, 11.0, 10.0, 18.0])
    model = noncentered_eight_schools if args.noncentered else centered_eight_schools
    kernel = NUTS(model, target_accept_prob=args.target_accept_prob)
    mcmc = MCMC(
        kernel,
        num_warmup=args.num_warmup,
        num_samples=args.num_samples,
        num_chains=1,
        progress_bar=not args.no_progress_bar,
    )
    mcmc.run(random.key(args.seed), len(y), sigma, y, extra_fields=("potential_energy", "num_steps"))
    samples = mcmc.get_samples()
    extra = mcmc.get_extra_fields()

    assert set(["mu", "tau"]).issubset(samples), f"missing sample keys: {samples.keys()}"
    assert samples["mu"].shape == (args.num_samples,)
    assert samples["theta"].shape[0] == args.num_samples
    assert "potential_energy" in extra and extra["potential_energy"].shape == (args.num_samples,)
    assert "num_steps" in extra and extra["num_steps"].shape == (args.num_samples,)

    result = {
        "sample_keys": sorted(samples.keys()),
        "mu_mean": float(jnp.mean(samples["mu"])),
        "tau_mean": float(jnp.mean(samples["tau"])),
        "potential_energy_shape": tuple(extra["potential_energy"].shape),
        "num_steps_shape": tuple(extra["num_steps"].shape),
        "noncentered": args.noncentered,
    }

    if args.predict_new_school:
        predictive = Predictive(new_school, posterior_samples={"mu": samples["mu"], "tau": samples["tau"]})
        pred = predictive(random.key(args.seed + 1))["obs"]
        assert pred.shape == (args.num_samples,)
        result["predictive_obs_shape"] = tuple(pred.shape)
        result["predictive_obs_mean"] = float(jnp.mean(pred))

    print("eight_schools_smoke ok")
    print(result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Tiny NumPyro NUTS/MCMC eight-schools smoke test.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--num-warmup", type=int, default=20)
    parser.add_argument("--num-samples", type=int, default=30)
    parser.add_argument("--target-accept-prob", type=float, default=0.8)
    parser.add_argument("--noncentered", action="store_true", help="Use LocScaleReparam non-centered theta site.")
    parser.add_argument("--predict-new-school", action="store_true", help="Also run a posterior predictive smoke.")
    parser.add_argument("--platform", choices=["cpu", "gpu", "tpu"], default=None)
    parser.add_argument("--x64", action="store_true")
    parser.add_argument("--no-progress-bar", action="store_true", default=True)
    args = parser.parse_args()
    if args.num_warmup < 0 or args.num_samples < 1:
        raise SystemExit("warmup must be nonnegative and samples must be positive")
    run(args)


if __name__ == "__main__":
    main()
