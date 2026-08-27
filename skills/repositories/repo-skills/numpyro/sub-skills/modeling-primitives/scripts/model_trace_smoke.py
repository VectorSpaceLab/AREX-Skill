#!/usr/bin/env python3
"""CPU-safe NumPyro model trace smoke test.

This helper validates three modeling-primitives facts without running MCMC/SVI:
1. handlers.seed gives deterministic random sample values.
2. handlers.condition marks a sample site observed.
3. handlers.trace exposes sample and deterministic site metadata.

Example:
    python model_trace_smoke.py
    python model_trace_smoke.py --num-observations 5 --seed 3
"""

from __future__ import annotations

import argparse

from jax import random
import jax.numpy as jnp

import numpyro
from numpyro import handlers
import numpyro.distributions as dist


def model(x: jnp.ndarray, y: jnp.ndarray | None = None) -> None:
    loc = numpyro.sample("loc", dist.Normal(0.0, 1.0))
    scale = numpyro.sample("scale", dist.LogNormal(0.0, 0.25))
    numpyro.deterministic("mean", loc + 0.0 * jnp.mean(x))
    with numpyro.plate("data", x.shape[0]):
        numpyro.sample("obs", dist.Normal(loc, scale), obs=y)


def run(seed: int, num_observations: int) -> None:
    x = jnp.linspace(-1.0, 1.0, num_observations)
    y = 0.5 + 0.1 * x

    seeded_once = handlers.trace(handlers.seed(model, random.key(seed))).get_trace(x, y)
    seeded_twice = handlers.trace(handlers.seed(model, random.key(seed))).get_trace(x, y)
    assert jnp.allclose(seeded_once["loc"]["value"], seeded_twice["loc"]["value"]), (
        "same seed should reproduce latent sample values"
    )

    conditioned = handlers.condition(model, {"loc": jnp.array(1.25), "obs": y})
    trace = handlers.trace(handlers.seed(conditioned, random.key(seed + 1))).get_trace(x)

    assert trace["loc"]["is_observed"], "conditioned latent site should be observed"
    assert float(trace["loc"]["value"]) == 1.25
    assert trace["obs"]["is_observed"], "conditioned obs site should be observed"
    assert trace["obs"]["value"].shape == (num_observations,)
    assert trace["mean"]["type"] == "deterministic"
    assert "data" in [frame.name for frame in trace["obs"]["cond_indep_stack"]]

    site_summary = {
        name: {
            "type": site["type"],
            "is_observed": site.get("is_observed"),
            "shape": tuple(getattr(site.get("value"), "shape", ())),
        }
        for name, site in trace.items()
    }
    print("model_trace_smoke ok")
    print(site_summary)


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test NumPyro handlers.seed/condition/trace metadata.")
    parser.add_argument("--seed", type=int, default=0, help="JAX PRNG seed.")
    parser.add_argument("--num-observations", type=int, default=4, help="Tiny observation count.")
    args = parser.parse_args()
    if args.num_observations < 1:
        raise SystemExit("--num-observations must be positive")
    run(args.seed, args.num_observations)


if __name__ == "__main__":
    main()
