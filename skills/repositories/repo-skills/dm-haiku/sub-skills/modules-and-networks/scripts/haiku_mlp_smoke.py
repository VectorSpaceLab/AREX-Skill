#!/usr/bin/env python3
"""Run a no-download Haiku MLP smoke check on synthetic data.

This helper adapts the model-construction pattern from Haiku's public MNIST
style examples while deliberately avoiding datasets, Optax, TensorFlow, TFDS,
network access, and training loops. It verifies that Haiku/JAX can initialize
and apply a tiny model, then reports output and parameter shapes.

Examples:
  python haiku_mlp_smoke.py
  python haiku_mlp_smoke.py --batch-size 4 --input-size 16 --hidden-sizes 8,4 --num-classes 3
"""

from __future__ import annotations

import argparse
import json
from typing import Sequence

import haiku as hk
import jax
import jax.numpy as jnp


def _parse_sizes(value: str) -> list[int]:
    sizes = [int(part.strip()) for part in value.split(",") if part.strip()]
    if not sizes:
        raise argparse.ArgumentTypeError("provide at least one hidden size")
    if any(size <= 0 for size in sizes):
        raise argparse.ArgumentTypeError("hidden sizes must be positive")
    return sizes


def _shape_tree(params) -> dict[str, dict[str, list[int]]]:
    return {
        module: {name: list(value.shape) for name, value in leaves.items()}
        for module, leaves in params.items()
    }


def run_smoke(batch_size: int, input_size: int, hidden_sizes: Sequence[int], num_classes: int) -> dict:
    if batch_size <= 0 or input_size <= 0 or num_classes <= 0:
        raise ValueError("batch-size, input-size, and num-classes must be positive")

    output_sizes = [*hidden_sizes, num_classes]

    def forward(x):
        model = hk.nets.MLP(output_sizes, name="mlp_probe")
        return model(x)

    network = hk.without_apply_rng(hk.transform(forward))
    x = jnp.linspace(-1.0, 1.0, batch_size * input_size, dtype=jnp.float32).reshape(
        batch_size, input_size
    )
    params = network.init(jax.random.PRNGKey(0), x)
    logits = network.apply(params, x)

    expected_shape = (batch_size, num_classes)
    if tuple(logits.shape) != expected_shape:
        raise AssertionError(f"logits shape {tuple(logits.shape)} != {expected_shape}")
    leaves = jax.tree_util.tree_leaves(params)
    if not leaves:
        raise AssertionError("MLP should create parameter leaves")

    return {
        "ok": True,
        "backend": jax.default_backend(),
        "input_shape": list(x.shape),
        "output_shape": list(logits.shape),
        "output_sizes": output_sizes,
        "param_tree": _shape_tree(params),
        "num_param_leaves": len(leaves),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=2, help="Synthetic batch size.")
    parser.add_argument("--input-size", type=int, default=8, help="Number of input features.")
    parser.add_argument(
        "--hidden-sizes",
        type=_parse_sizes,
        default=[16, 8],
        help="Comma-separated hidden layer widths, for example 32,16.",
    )
    parser.add_argument("--num-classes", type=int, default=5, help="Output/logit width.")
    args = parser.parse_args()
    print(json.dumps(run_smoke(args.batch_size, args.input_size, args.hidden_sizes, args.num_classes), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
