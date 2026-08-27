#!/usr/bin/env python3
"""Quick Optax environment and API sanity checks.

This helper is meant for future agents who need a fast way to confirm that
Optax, JAX, and a few representative APIs are importable before they choose a
more expensive workflow.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from typing import Any


def _signature(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "<no signature available>"


def _summary() -> dict[str, Any]:
    import jax
    import optax

    from optax import assignment, losses, projections, schedules, tree_utils

    selected = {
        "adam": optax.adam,
        "chain": optax.chain,
        "apply_updates": optax.apply_updates,
        "softmax_cross_entropy": losses.softmax_cross_entropy,
        "cosine_decay_schedule": schedules.cosine_decay_schedule,
        "projection_simplex": projections.projection_simplex,
        "hungarian_algorithm": assignment.hungarian_algorithm,
        "tree_add": tree_utils.tree_add,
    }

    return {
        "optax_version": getattr(optax, "__version__", "unknown"),
        "jax_version": jax.__version__,
        "jax_backend": jax.default_backend(),
        "jax_devices": [str(device) for device in jax.devices()],
        "export_count": len(getattr(optax, "__all__", ())),
        "signatures": {name: _signature(obj) for name, obj in selected.items()},
    }


def _smoke() -> dict[str, Any]:
    import jax
    import jax.numpy as jnp
    import optax

    from optax import assignment, losses, projections, schedules, tree_utils

    params = {"w": jnp.array([1.0, -1.0], dtype=jnp.float32)}
    grads = {"w": jnp.array([0.1, -0.2], dtype=jnp.float32)}

    tx = optax.chain(
        optax.clip_by_global_norm(1.0),
        optax.adam(1e-2),
    )
    state = tx.init(params)
    updates, state = tx.update(grads, state, params)
    new_params = optax.apply_updates(params, updates)

    schedule = schedules.cosine_decay_schedule(1.0, decay_steps=10)
    loss_value = losses.l2_loss(jnp.array(2.0), jnp.array(1.0))
    simplex = projections.projection_simplex(jnp.array([-1.0, 0.5, 2.0]))
    assignment_result = assignment.hungarian_algorithm(
        jnp.array([[2.0, 1.0], [1.0, 2.0]], dtype=jnp.float32)
    )
    tree_sum = tree_utils.tree_add(
        {"w": jnp.array([1.0, 2.0])}, {"w": jnp.array([3.0, 4.0])}
    )

    return {
        "updated_params": jax.tree_util.tree_map(lambda x: x.tolist(), new_params),
        "schedule_step_0": float(schedule(0)),
        "schedule_step_5": float(schedule(5)),
        "loss_value": float(loss_value),
        "simplex": simplex.tolist(),
        "assignment": [leaf.tolist() for leaf in assignment_result],
        "tree_sum": jax.tree_util.tree_map(lambda x: x.tolist(), tree_sum),
        "state_type": type(state).__name__,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check a tiny Optax + JAX environment and sample APIs."
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run a tiny end-to-end optimizer and helper smoke check.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of formatted text.",
    )
    args = parser.parse_args()

    try:
        summary = _summary()
    except Exception as exc:  # pragma: no cover - defensive environment check
        print(f"optax doctor: import check failed: {exc}", file=sys.stderr)
        return 1

    payload: dict[str, Any] = {"summary": summary}
    if args.smoke:
        try:
            payload["smoke"] = _smoke()
        except Exception as exc:  # pragma: no cover - defensive environment check
            print(f"optax doctor: smoke check failed: {exc}", file=sys.stderr)
            return 1

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"optax version: {summary['optax_version']}")
        print(f"jax version: {summary['jax_version']}")
        print(f"jax backend: {summary['jax_backend']}")
        print(f"jax devices: {', '.join(summary['jax_devices'])}")
        print(f"optax exports: {summary['export_count']}")
        for name, sig in summary["signatures"].items():
            print(f"{name}: {sig}")
        if args.smoke:
            print("smoke:")
            for key, value in payload["smoke"].items():
                print(f"  {key}: {value}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
