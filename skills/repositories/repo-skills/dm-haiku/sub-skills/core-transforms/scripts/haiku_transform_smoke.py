#!/usr/bin/env python3
"""Deterministic smoke checks for Haiku core transforms.

Purpose:
  Verify a local Haiku/JAX installation can run stateless transforms, stateful
  transforms, multi-transform shared init/apply, and hk.running_init() behavior
  on tiny synthetic arrays. The script performs no network, file, or dataset IO.

Examples:
  python haiku_transform_smoke.py --mode all
  python haiku_transform_smoke.py --mode stateless
  python haiku_transform_smoke.py --mode stateful
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable

import haiku as hk
import jax
import jax.numpy as jnp


def _assert_shape(value, expected: Iterable[int], label: str) -> None:
    actual = tuple(value.shape)
    expected = tuple(expected)
    assert actual == expected, f"{label} shape {actual} != expected {expected}"


def _assert_scalar_value(value, expected: int, label: str) -> None:
    actual = int(jax.device_get(value))
    assert actual == expected, f"{label} value {actual} != expected {expected}"


def _assert_empty_tree(tree, label: str) -> None:
    leaves = jax.tree_util.tree_leaves(tree)
    assert not leaves, f"{label} expected empty tree, got leaves={leaves!r}"


def run_stateless() -> list[str]:
    """Check hk.transform, hk.without_apply_rng, and hk.with_empty_state."""

    def forward(x):
        return hk.Linear(3, name="linear")(x)

    x = jnp.ones([2, 4], dtype=jnp.float32)
    key = jax.random.PRNGKey(0)

    transformed = hk.transform(forward)
    params = transformed.init(key, x)
    y = transformed.apply(params, None, x)
    _assert_shape(y, (2, 3), "stateless apply output")
    _assert_shape(params["linear"]["w"], (4, 3), "linear/w")
    _assert_shape(params["linear"]["b"], (3,), "linear/b")

    no_rng = hk.without_apply_rng(hk.transform(forward))
    params_no_rng = no_rng.init(key, x)
    y_no_rng = no_rng.apply(params_no_rng, x)
    _assert_shape(y_no_rng, (2, 3), "without_apply_rng output")

    empty_state = hk.with_empty_state(hk.transform(forward))
    params_empty, state_empty = empty_state.init(key, x)
    y_empty, state_empty = empty_state.apply(params_empty, state_empty, None, x)
    _assert_shape(y_empty, (2, 3), "with_empty_state output")
    _assert_empty_tree(state_empty, "with_empty_state returned state")

    guarded = hk.without_state(hk.transform_with_state(forward))
    params_guarded = guarded.init(key, x)
    y_guarded = guarded.apply(params_guarded, None, x)
    _assert_shape(y_guarded, (2, 3), "without_state output")

    return ["stateless", "without_apply_rng", "with_empty_state", "without_state"]


def run_stateful() -> list[str]:
    """Check hk.transform_with_state argument order and state updates."""

    def counter_forward(x):
        count = hk.get_state("count", shape=[], dtype=jnp.int32, init=jnp.zeros)
        hk.set_state("count", count + 1)
        scale = hk.get_parameter("scale", shape=[x.shape[-1]], dtype=x.dtype, init=jnp.ones)
        return x * scale + count.astype(x.dtype)

    x = jnp.ones([2, 3], dtype=jnp.float32)
    key = jax.random.PRNGKey(1)
    transformed = hk.transform_with_state(counter_forward)

    params, state = transformed.init(key, x)
    _assert_shape(params["~"]["scale"], (3,), "stateful scale parameter")
    _assert_shape(state["~"]["count"], (), "initial count state")
    _assert_scalar_value(state["~"]["count"], 0, "initial count state")

    y, new_state = transformed.apply(params, state, None, x)
    _assert_shape(y, (2, 3), "stateful apply output")
    _assert_shape(new_state["~"]["count"], (), "updated count state")
    _assert_scalar_value(new_state["~"]["count"], 1, "updated count state")

    no_apply_rng = hk.without_apply_rng(hk.transform_with_state(counter_forward))
    params2, state2 = no_apply_rng.init(key, x)
    y2, state2 = no_apply_rng.apply(params2, state2, x)
    _assert_shape(y2, (2, 3), "stateful without_apply_rng output")
    _assert_scalar_value(state2["~"]["count"], 1, "stateful without_apply_rng state")

    return ["stateful", "stateful_without_apply_rng"]


def run_multi_transform() -> list[str]:
    """Check multi_transform and multi_transform_with_state shared init/apply."""

    def stateless_factory():
        encoder = hk.Linear(2, name="encoder")
        decoder = hk.Linear(4, name="decoder")

        def template(x):
            return decoder(encoder(x))

        def encode(x):
            return encoder(x)

        def decode(z):
            return decoder(z)

        return template, {"encode": encode, "decode": decode}

    x = jnp.ones([2, 3], dtype=jnp.float32)
    key = jax.random.PRNGKey(2)
    multi = hk.without_apply_rng(hk.multi_transform(stateless_factory))
    params = multi.init(key, x)
    z = multi.apply["encode"](params, x)
    y = multi.apply["decode"](params, z)
    _assert_shape(params["encoder"]["w"], (3, 2), "multi encoder/w")
    _assert_shape(params["decoder"]["w"], (2, 4), "multi decoder/w")
    _assert_shape(z, (2, 2), "multi encode output")
    _assert_shape(y, (2, 4), "multi decode output")

    def stateful_factory():
        def bump(x):
            count = hk.get_state("count", shape=[], dtype=jnp.int32, init=jnp.zeros)
            hk.set_state("count", count + 1)
            return x + count.astype(x.dtype)

        def template(x):
            return bump(x)

        return template, {"bump": bump}

    multi_state = hk.without_apply_rng(hk.multi_transform_with_state(stateful_factory))
    params_s, state_s = multi_state.init(key, x)
    y_s, state_s = multi_state.apply["bump"](params_s, state_s, x)
    _assert_shape(y_s, (2, 3), "multi stateful bump output")
    _assert_shape(state_s["~"]["count"], (), "multi stateful count")
    _assert_scalar_value(state_s["~"]["count"], 1, "multi stateful count")

    return ["multi_transform", "multi_transform_with_state"]


def run_running_init() -> list[str]:
    """Check hk.running_init initializes both conditional branches."""

    def conditional_forward(x, use_left: bool):
        left = hk.Linear(2, name="left")
        right = hk.Linear(2, name="right")
        if hk.running_init():
            _ = left(x)
            _ = right(x)
        return left(x) if use_left else right(x)

    x = jnp.ones([1, 3], dtype=jnp.float32)
    key = jax.random.PRNGKey(3)
    transformed = hk.transform(conditional_forward)
    params = transformed.init(key, x, True)
    assert set(params.keys()) == {"left", "right"}, f"conditional params keys={set(params.keys())!r}"
    y = transformed.apply(params, None, x, False)
    _assert_shape(y, (1, 2), "running_init alternate branch output")

    return ["running_init"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("all", "stateless", "stateful"),
        default="all",
        help="Subset of deterministic Haiku transform smoke checks to run.",
    )
    args = parser.parse_args(argv)

    checks: list[str] = []
    if args.mode in ("all", "stateless"):
        checks.extend(run_stateless())
    if args.mode in ("all", "stateful"):
        checks.extend(run_stateful())
    if args.mode == "all":
        checks.extend(run_multi_transform())
        checks.extend(run_running_init())

    print("haiku_transform_smoke: OK", ", ".join(checks))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"haiku_transform_smoke: ASSERTION FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
