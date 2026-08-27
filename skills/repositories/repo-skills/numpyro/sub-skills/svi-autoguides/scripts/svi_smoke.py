#!/usr/bin/env python3
"""Tiny CPU-safe NumPyro SVI smoke test.

This adapts NumPyro's minimal SVI example to use synthetic data, a manual guide,
finite-loss assertions, and configurable small step counts. It does not require
network, plotting, optional dependencies, or the source checkout.
"""

from __future__ import annotations

import argparse

from jax import random
import jax.numpy as jnp

import numpyro
from numpyro import optim
import numpyro.distributions as dist
from numpyro.distributions import constraints
from numpyro.infer import SVI, Trace_ELBO, Predictive
from numpyro.util import fori_loop


def model(data: jnp.ndarray) -> None:
    loc = numpyro.sample("loc", dist.Normal(0.0, 2.0))
    scale = numpyro.sample("scale", dist.LogNormal(0.0, 0.25))
    with numpyro.plate("data", data.shape[0]):
        numpyro.sample("obs", dist.Normal(loc, scale), obs=data)


def guide(data: jnp.ndarray) -> None:
    guide_loc = numpyro.param("guide_loc", 0.0)
    guide_scale = numpyro.param("guide_scale", 0.5, constraint=constraints.positive)
    guide_obs_scale = numpyro.param("guide_obs_scale", 1.0, constraint=constraints.positive)
    numpyro.sample("loc", dist.Normal(guide_loc, guide_scale))
    numpyro.sample("scale", dist.LogNormal(jnp.log(guide_obs_scale), 0.1))


def run(args: argparse.Namespace) -> None:
    if args.x64:
        numpyro.enable_x64()
    key = random.key(args.seed)
    data = random.normal(key, shape=(args.num_data,)) * args.noise + args.target_loc

    svi = SVI(model, guide, optim.Adam(args.learning_rate), Trace_ELBO(num_particles=args.num_particles))
    state = svi.init(random.fold_in(key, 1), data)

    losses = []

    def body_fn(i, state_and_losses):
        state, losses = state_and_losses
        state, loss = svi.update(state, data)
        losses = losses.at[i].set(loss)
        return state, losses

    losses_init = jnp.zeros((args.num_steps,))
    state, losses = fori_loop(0, args.num_steps, body_fn, (state, losses_init))
    params = svi.get_params(state)

    assert bool(jnp.all(jnp.isfinite(losses))), "SVI losses must be finite"
    assert bool(jnp.isfinite(params["guide_loc"])), "guide_loc must be finite"
    assert params["guide_scale"] > 0, "guide_scale must satisfy positive constraint"
    assert abs(float(params["guide_loc"] - args.target_loc)) < args.tolerance, (
        f"guide_loc={float(params['guide_loc'])} did not approach target {args.target_loc}"
    )

    predictive = Predictive(model, guide=guide, params=params, num_samples=args.predictive_samples)
    pred = predictive(random.fold_in(key, 2), data=jnp.zeros((args.num_data,)))
    assert pred["obs"].shape == (args.predictive_samples, args.num_data)

    print("svi_smoke ok")
    print({
        "num_steps": args.num_steps,
        "final_loss": float(losses[-1]),
        "guide_loc": float(params["guide_loc"]),
        "guide_scale": float(params["guide_scale"]),
        "predictive_obs_shape": tuple(pred["obs"].shape),
    })


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test a tiny NumPyro SVI workflow.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--num-data", type=int, default=100)
    parser.add_argument("--num-steps", type=int, default=400)
    parser.add_argument("--learning-rate", type=float, default=0.02)
    parser.add_argument("--num-particles", type=int, default=10)
    parser.add_argument("--target-loc", type=float, default=3.0)
    parser.add_argument("--noise", type=float, default=0.1)
    parser.add_argument("--tolerance", type=float, default=0.35)
    parser.add_argument("--predictive-samples", type=int, default=5)
    parser.add_argument("--x64", action="store_true")
    args = parser.parse_args()
    if args.num_steps < 1 or args.num_data < 2 or args.predictive_samples < 1:
        raise SystemExit("num-steps, num-data, and predictive-samples must be positive")
    run(args)


if __name__ == "__main__":
    main()
