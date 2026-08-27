#!/usr/bin/env python3
"""CPU-safe NumPyro distribution and transform smoke test.

The script checks finite log probabilities, event-shape handling, transformed
support, and orthonormal transform round-trips. It is intentionally tiny and
runs without datasets, network, plotting, or inference.
"""

from __future__ import annotations

import argparse

from jax import random
import jax.numpy as jnp

import numpyro
import numpyro.distributions as dist
from numpyro.distributions import transforms
from numpyro.distributions.distribution import validation_enabled


def run(seed: int, size: int, check_x64: bool) -> None:
    if check_x64:
        numpyro.enable_x64()

    key = random.key(seed)
    normal = dist.Normal(jnp.zeros(size), jnp.ones(size))
    samples = normal.sample(key, sample_shape=(3,))
    logp = normal.log_prob(samples)
    assert samples.shape == (3, size)
    assert logp.shape == (3, size)
    assert bool(jnp.all(jnp.isfinite(logp)))

    vector_event = normal.to_event(1)
    vector_logp = vector_event.log_prob(samples)
    assert vector_event.event_shape == (size,)
    assert vector_logp.shape == (3,)

    with validation_enabled(True):
        beta = dist.Beta(2.0, 5.0, validate_args=True)
        value = jnp.array([0.2, 0.7])
        assert bool(jnp.all(beta.support.check(value)))
        assert bool(jnp.all(jnp.isfinite(beta.log_prob(value))))

    positive = dist.TransformedDistribution(dist.Normal(0.0, 1.0), transforms.ExpTransform())
    y = positive.sample(random.fold_in(key, 1), sample_shape=(size,))
    assert bool(jnp.all(y > 0))
    assert bool(jnp.all(jnp.isfinite(positive.log_prob(y))))

    x = random.normal(random.fold_in(key, 2), (2, max(size, 2)))
    for transform in [transforms.HaarTransform(), transforms.DiscreteCosineTransform()]:
        z = transform(x)
        assert bool(jnp.allclose(transform.inv(z), x, atol=1e-5, rtol=1e-5))
        assert bool(jnp.allclose(transform.log_abs_det_jacobian(x, z), 0.0, atol=1e-6))

    print("distribution_transform_smoke ok")
    print({
        "sample_shape": tuple(samples.shape),
        "batch_log_prob_shape": tuple(logp.shape),
        "event_log_prob_shape": tuple(vector_logp.shape),
        "x64_enabled": bool(jnp.asarray(0.0).dtype == jnp.float64),
    })


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test NumPyro distributions and transforms.")
    parser.add_argument("--seed", type=int, default=0, help="JAX PRNG seed.")
    parser.add_argument("--size", type=int, default=4, help="Small vector size for checks.")
    parser.add_argument("--x64", action="store_true", help="Enable x64 before running checks.")
    args = parser.parse_args()
    if args.size < 2:
        raise SystemExit("--size must be at least 2")
    run(args.seed, args.size, args.x64)


if __name__ == "__main__":
    main()
