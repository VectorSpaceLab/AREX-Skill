#!/usr/bin/env python3
"""Smoke-test Haiku-aware JAX transform wrappers and tree utilities.

The checks are synthetic and safe: no Graphviz, TensorFlow, datasets, network
access, or long-running compilation. They demonstrate wrapper usage inside a
Haiku transform and parameter-tree partition/merge utilities.

Examples:
  python haiku_jax_transform_smoke.py --mode all
  python haiku_jax_transform_smoke.py --mode vmap
  python haiku_jax_transform_smoke.py --mode data-structures
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import haiku as hk
import haiku.data_structures as hkds
import jax
import jax.numpy as jnp


def _shape_tree(tree: Any) -> dict[str, dict[str, list[int]]]:
    return {
        module: {name: list(value.shape) for name, value in leaves.items()}
        for module, leaves in tree.items()
    }


def check_vmap() -> dict[str, Any]:
    """Use hk.vmap inside hk.transform where the mapped function owns Haiku params."""

    def per_example(x):
        return hk.Linear(3, name="mapped_linear")(x)

    def forward(xs):
        return hk.vmap(per_example, split_rng=False)(xs)

    transformed = hk.without_apply_rng(hk.transform(forward))
    xs = jnp.ones([4, 5], dtype=jnp.float32)
    params = transformed.init(jax.random.PRNGKey(0), xs)
    ys = transformed.apply(params, xs)
    if tuple(ys.shape) != (4, 3):
        raise AssertionError(f"hk.vmap output shape {tuple(ys.shape)} != (4, 3)")
    return {"output_shape": list(ys.shape), "params": _shape_tree(params)}


def check_scan() -> dict[str, Any]:
    """Use hk.scan inside hk.transform for a recurrent-style carry."""

    def forward(sequence):
        cell = hk.Linear(2, name="scan_cell")

        def step(carry, x_t):
            new_carry = jnp.tanh(cell(x_t) + carry)
            return new_carry, new_carry

        initial = jnp.zeros([2], dtype=sequence.dtype)
        final, outputs = hk.scan(step, initial, sequence)
        return final, outputs

    transformed = hk.without_apply_rng(hk.transform(forward))
    sequence = jnp.ones([6, 4], dtype=jnp.float32)
    params = transformed.init(jax.random.PRNGKey(1), sequence)
    final, outputs = transformed.apply(params, sequence)
    if tuple(final.shape) != (2,) or tuple(outputs.shape) != (6, 2):
        raise AssertionError(f"unexpected scan shapes final={final.shape} outputs={outputs.shape}")
    return {"final_shape": list(final.shape), "outputs_shape": list(outputs.shape), "params": _shape_tree(params)}


def check_data_structures() -> dict[str, Any]:
    """Partition and merge a Haiku-style parameter tree."""

    params = hkds.to_immutable_dict(
        {
            "encoder/linear": {"w": jnp.ones([3, 2]), "b": jnp.zeros([2])},
            "head/linear": {"w": jnp.ones([2, 1]), "b": jnp.zeros([1])},
        }
    )
    encoder, head = hkds.partition(lambda module, name, value: module.startswith("encoder"), params)
    merged = hkds.merge(encoder, head)
    if set(encoder.keys()) != {"encoder/linear"}:
        raise AssertionError(f"encoder partition mismatch: {list(encoder.keys())}")
    if set(head.keys()) != {"head/linear"}:
        raise AssertionError(f"head partition mismatch: {list(head.keys())}")
    if set(merged.keys()) != set(params.keys()):
        raise AssertionError("merged tree keys did not match original keys")
    return {
        "encoder_keys": sorted(encoder.keys()),
        "head_keys": sorted(head.keys()),
        "merged_tree_size_bytes": int(hkds.tree_bytes(merged)),
    }


CHECKS = {
    "vmap": check_vmap,
    "scan": check_scan,
    "data-structures": check_data_structures,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("all", *CHECKS.keys()),
        default="all",
        help="Subset of advanced Haiku checks to run.",
    )
    args = parser.parse_args()
    modes = list(CHECKS) if args.mode == "all" else [args.mode]
    result = {mode: CHECKS[mode]() for mode in modes}
    print(json.dumps({"ok": True, "backend": jax.default_backend(), "checks": result}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
