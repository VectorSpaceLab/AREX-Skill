#!/usr/bin/env python3
"""Tiny Equinox smoke checks for generated repo-skill users.

This script is intentionally self-contained: it imports the installed Equinox
package and runs small CPU-safe checks without reading the original repository.
It is not a replacement for the repository's full test suite.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from collections.abc import Callable


MODES = ("module", "transformations", "nn", "diagnostics", "internal", "all")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=MODES,
        default="all",
        help="Which smoke check group to run.",
    )
    parser.add_argument(
        "--two-cpu-devices",
        action="store_true",
        help=(
            "Before importing JAX, request two logical CPU devices via XLA_FLAGS. "
            "Useful for filter_pmap/sharding smoke checks in a CPU-only process."
        ),
    )
    return parser.parse_args()


def configure_before_jax(args: argparse.Namespace) -> None:
    if args.two_cpu_devices:
        existing = os.environ.get("XLA_FLAGS", "")
        flag = "--xla_force_host_platform_device_count=2"
        if flag not in existing:
            os.environ["XLA_FLAGS"] = f"{existing} {flag}".strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def imports():
    import equinox as eqx
    import equinox.internal as eqxi
    import jax
    import jax.numpy as jnp

    return eqx, eqxi, jax, jnp


def run_module() -> None:
    eqx, _, jax, jnp = imports()

    class Affine(eqx.Module):
        weight: jax.Array
        bias: jax.Array
        name: str = eqx.field(static=True)

        def __init__(self, name: str = "affine"):
            self.weight = jnp.array([[1.0, 2.0], [3.0, 4.0]])
            self.bias = jnp.array([0.5, -0.5])
            self.name = name

        def __call__(self, x):
            return self.weight @ x + self.bias

    module = Affine()
    eqx.tree_check(module)
    params, static = eqx.partition(module, eqx.is_array)
    restored = eqx.combine(params, static)
    require(restored.name == module.name, "partition/combine static field mismatch")
    require(
        bool(eqx.tree_equal(restored(jnp.ones(2)), module(jnp.ones(2)))),
        "partition/combine callable output mismatch",
    )

    updated = eqx.tree_at(lambda m: m.bias, module, jnp.array([1.0, 1.0]))
    require(updated(jnp.ones(2)).shape == (2,), "tree_at-updated module call failed")
    print("module: ok")


def run_transformations() -> None:
    eqx, _, jax, jnp = imports()

    class Model(eqx.Module):
        layer: eqx.nn.Linear
        activation: Callable = eqx.field(static=True)

        def __init__(self):
            self.layer = eqx.nn.Linear(2, 1, key=jax.random.PRNGKey(0))
            self.activation = jax.nn.tanh

        def __call__(self, x):
            return self.activation(self.layer(x))[0]

    model = Model()

    @eqx.filter_jit
    def value(m, x):
        return m(x)

    grad_model = eqx.filter_grad(lambda m, x: value(m, x))(model, jnp.ones(2))
    require(eqx.filter(grad_model, eqx.is_array) is not None, "filter_grad returned no array structure")

    batched = eqx.filter_vmap(lambda x: value(model, x))(jnp.ones((3, 2)))
    require(batched.shape == (3,), "filter_vmap batch shape mismatch")

    shape = eqx.filter_eval_shape(lambda m, x: value(m, x), model, jnp.ones(2))
    require(shape.shape == (), "filter_eval_shape scalar output mismatch")

    if len(jax.devices()) >= 2:
        out = eqx.filter_pmap(lambda x: x + 1)(jnp.arange(len(jax.devices())))
        require(out.shape[0] == len(jax.devices()), "filter_pmap output shape mismatch")
        print(f"transformations: ok including pmap over {len(jax.devices())} devices")
    else:
        print("transformations: ok; skipped pmap because fewer than two devices are visible")


def run_nn() -> None:
    eqx, _, jax, jnp = imports()

    key = jax.random.PRNGKey(0)
    mlp = eqx.nn.MLP(2, 1, 4, 2, key=key)
    require(mlp(jnp.ones(2)).shape == (1,), "MLP output shape mismatch")

    seq = eqx.nn.Sequential(
        [
            eqx.nn.Linear(2, 3, key=key),
            eqx.nn.Lambda(jax.nn.relu),
            eqx.nn.Linear(3, 1, key=key),
        ]
    )
    require(seq(jnp.ones(2)).shape == (1,), "Sequential output shape mismatch")

    class Counter(eqx.Module):
        index: eqx.nn.StateIndex

        def __init__(self):
            self.index = eqx.nn.StateIndex(jnp.array(0))

        def __call__(self, x, state):
            current = state.get(self.index)
            return x + current, state.set(self.index, current + 1)

    counter, state = eqx.nn.make_with_state(Counter)()
    _, state = counter(jnp.array(1.0), state)
    require(state.get(counter.index).item() == 1, "StateIndex update failed")

    pair = (eqx.nn.Embedding(4, 3, key=key), eqx.nn.Linear(3, 4, key=key))
    shared = eqx.nn.Shared(pair, lambda p: p[1].weight, lambda p: p[0].weight)
    embedding, linear = shared()
    require(embedding.weight is linear.weight, "Shared did not tie target weight")
    print("nn: ok")


def run_diagnostics() -> None:
    eqx, _, jax, jnp = imports()

    tree = (jnp.array([1.0, 2.0]), {"bias": jnp.array(3.0)}, "metadata")
    like = (jnp.zeros(2), {"bias": jnp.array(0.0)}, "like-metadata")
    with tempfile.TemporaryDirectory() as tmpdir:
        eqx.tree_serialise_leaves(tmpdir, tree)
        restored = eqx.tree_deserialise_leaves(tmpdir, like)
    require(bool(eqx.tree_equal(restored[:2], tree[:2])), "serialization round-trip failed")
    require(restored[2] == "like-metadata", "non-array leaf did not come from like-tree")

    token = eqx.error_if(jnp.array(1.0), False, "should not raise")
    require(float(token) == 1.0, "error_if false branch changed token")

    formatted = eqx.tree_pformat(tree)
    require("metadata" in formatted, "tree_pformat did not include metadata leaf")

    @jax.jit
    @eqx.debug.assert_max_traces(max_traces=2)
    def f(x):
        return x + 1

    f(jnp.array(1.0))
    f(jnp.array(2.0))
    require(eqx.debug.get_num_traces(f) == 1, "trace counting smoke failed")
    print("diagnostics: ok")


def run_internal() -> None:
    eqx, eqxi, jax, jnp = imports()

    @eqxi.noinline
    def add_one(x):
        return x + 1

    require(int(add_one(jnp.array(1))) == 2, "noinline smoke failed")

    out = eqxi.while_loop(
        lambda x: x < 3,
        lambda x: x + 1,
        jnp.array(0),
        kind="bounded",
        max_steps=4,
    )
    require(int(out) == 3, "internal while_loop smoke failed")

    carry, ys = eqxi.scan(
        lambda c, x: (c + x, c + x),
        jnp.array(0),
        jnp.arange(4),
        kind="lax",
    )
    require(int(carry) == 6 and ys.shape == (4,), "internal scan smoke failed")

    token = eqxi.nontraceable((jnp.array(1.0), "static"))
    require(token[1] == "static", "nontraceable smoke changed static leaf")
    print("internal: ok")


def main() -> int:
    args = parse_args()
    configure_before_jax(args)

    selected = MODES[:-1] if args.mode == "all" else (args.mode,)
    runners = {
        "module": run_module,
        "transformations": run_transformations,
        "nn": run_nn,
        "diagnostics": run_diagnostics,
        "internal": run_internal,
    }
    try:
        for mode in selected:
            runners[mode]()
    except Exception as exc:  # pragma: no cover - diagnostic CLI path
        print(f"Equinox smoke check failed in mode {args.mode}: {exc}", file=sys.stderr)
        return 1
    print("all requested Equinox smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
