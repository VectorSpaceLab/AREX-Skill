#!/usr/bin/env python3
"""Deterministic Haiku smoke checks for parameters, state, and RNG APIs."""

from __future__ import annotations

import argparse
import json
from typing import Any

import haiku as hk
import jax
import jax.numpy as jnp


def _shape_tree(tree: Any) -> dict[str, dict[str, list[int]]]:
    """Return a JSON-friendly module/leaf shape tree."""
    out: dict[str, dict[str, list[int]]] = {}
    for module_name, leaves in tree.items():
        out[module_name] = {}
        for leaf_name, value in leaves.items():
            out[module_name][leaf_name] = list(value.shape)
    return out


def _scalar_int(value: Any) -> int:
    return int(jax.device_get(value).item())


def _assert_allclose(left: Any, right: Any, message: str) -> None:
    if not bool(jnp.allclose(left, right)):
        raise AssertionError(message)


def run_params() -> dict[str, Any]:
    """Verify a custom Module creates expected parameter keys and shapes."""

    class AffineProbe(hk.Module):
        def __init__(self, width: int, name: str | None = None):
            super().__init__(name=name)
            self.width = width

        def __call__(self, x):
            w = hk.get_parameter(
                "w",
                [x.shape[-1], self.width],
                dtype=x.dtype,
                init=hk.initializers.Constant(0.5),
            )
            b = hk.get_parameter(
                "b", [self.width], dtype=x.dtype, init=jnp.zeros
            )
            return jnp.dot(x, w) + b

    def forward(x):
        with hk.name_scope("outer"):
            return AffineProbe(width=2, name="affine")(x)

    transformed = hk.without_apply_rng(hk.transform(forward))
    x = jnp.arange(6, dtype=jnp.float32).reshape(2, 3)
    params = transformed.init(jax.random.PRNGKey(0), x)

    expected_module = "outer/affine"
    if set(params.keys()) != {expected_module}:
        raise AssertionError(f"unexpected parameter modules: {list(params.keys())}")
    if set(params[expected_module].keys()) != {"w", "b"}:
        raise AssertionError(f"unexpected leaves: {list(params[expected_module].keys())}")
    if tuple(params[expected_module]["w"].shape) != (3, 2):
        raise AssertionError("weight shape should be (3, 2)")
    if tuple(params[expected_module]["b"].shape) != (2,):
        raise AssertionError("bias shape should be (2,)")

    y = transformed.apply(params, x)
    expected = jnp.dot(x, jnp.full((3, 2), 0.5, dtype=x.dtype))
    _assert_allclose(y, expected, "AffineProbe output did not match constants")

    return {
        "modules": sorted(params.keys()),
        "shapes": _shape_tree(params),
        "output_shape": list(y.shape),
    }


def run_state() -> dict[str, Any]:
    """Verify mutable state updates under transform_with_state."""

    class Counter(hk.Module):
        def __call__(self, x):
            count = hk.get_state(
                "count", shape=[], dtype=jnp.int32, init=jnp.zeros
            )
            total = hk.get_state(
                "total", shape=x.shape, dtype=x.dtype, init=jnp.zeros
            )
            hk.set_state("count", count + 1)
            hk.set_state("total", total + x)
            return x + count.astype(x.dtype)

    def forward(x):
        return Counter(name="counter")(x)

    transformed = hk.transform_with_state(forward)
    x = jnp.ones([2, 3], dtype=jnp.float32)
    params, state0 = transformed.init(None, x)

    if len(params) != 0:
        raise AssertionError(f"counter should not create params: {params}")
    if set(state0.keys()) != {"counter"}:
        raise AssertionError(f"unexpected state modules: {list(state0.keys())}")
    if _scalar_int(state0["counter"]["count"]) != 0:
        raise AssertionError("initial count should be 0")
    _assert_allclose(
        state0["counter"]["total"], jnp.zeros_like(x), "initial total should be zero"
    )

    y1, state1 = transformed.apply(params, state0, None, x)
    y2, state2 = transformed.apply(params, state1, None, x)

    _assert_allclose(y1, x, "first call should add count 0")
    _assert_allclose(y2, x + 1, "second call should add count 1")
    if _scalar_int(state1["counter"]["count"]) != 1:
        raise AssertionError("count after first apply should be 1")
    if _scalar_int(state2["counter"]["count"]) != 2:
        raise AssertionError("count after second apply should be 2")
    _assert_allclose(state2["counter"]["total"], 2 * x, "total should accumulate")

    return {
        "initial_shapes": _shape_tree(state0),
        "count_after_first_apply": _scalar_int(state1["counter"]["count"]),
        "count_after_second_apply": _scalar_int(state2["counter"]["count"]),
        "output_shapes": [list(y1.shape), list(y2.shape)],
    }


def run_rng() -> dict[str, Any]:
    """Verify required RNG failure/recovery and optional RNG fallback."""

    def required_rng_forward(x):
        key = hk.next_rng_key()
        return x + jax.random.normal(key, x.shape)

    required = hk.transform(required_rng_forward)
    x = jnp.zeros([2, 3], dtype=jnp.float32)
    params = required.init(jax.random.PRNGKey(1), x)

    missing_error = None
    try:
        required.apply(params, None, x)
    except ValueError as exc:
        missing_error = str(exc)

    if missing_error is None or "non-None PRNGKey" not in missing_error:
        raise AssertionError("required RNG path should fail with rng=None")

    y_a = required.apply(params, jax.random.PRNGKey(2), x)
    y_b = required.apply(params, jax.random.PRNGKey(2), x)
    y_c = required.apply(params, jax.random.PRNGKey(3), x)
    _assert_allclose(y_a, y_b, "same apply key should reproduce the same sample")
    if bool(jnp.allclose(y_a, y_c)):
        raise AssertionError("different apply keys unexpectedly produced same sample")

    def optional_rng_forward(x):
        key = hk.maybe_next_rng_key()
        if key is None:
            return x
        return x + jax.random.uniform(key, x.shape)

    optional = hk.transform(optional_rng_forward)
    optional_params = optional.init(None, x)
    deterministic = optional.apply(optional_params, None, x)
    stochastic = optional.apply(optional_params, jax.random.PRNGKey(4), x)
    _assert_allclose(deterministic, x, "maybe_next_rng_key fallback should be deterministic")
    if bool(jnp.allclose(stochastic, x)):
        raise AssertionError("optional RNG path with a key should perturb x")

    return {
        "required_rng_missing_error_contains": "non-None PRNGKey",
        "required_rng_output_shape": list(y_a.shape),
        "optional_no_rng_shape": list(deterministic.shape),
        "optional_with_rng_shape": list(stochastic.shape),
    }


CHECKS = {
    "params": run_params,
    "state": run_state,
    "rng": run_rng,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Smoke-test Haiku Module parameter, state, and RNG behavior."
    )
    parser.add_argument(
        "--mode",
        choices=("all", "params", "state", "rng"),
        default="all",
        help="Which check group to run.",
    )
    args = parser.parse_args()

    modes = list(CHECKS) if args.mode == "all" else [args.mode]
    result = {mode: CHECKS[mode]() for mode in modes}
    print(json.dumps({"ok": True, "checks": result}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
