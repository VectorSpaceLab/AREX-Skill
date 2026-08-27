#!/usr/bin/env python3
"""Smoke-check Haiku's optional Flax interop path on synthetic data."""

from __future__ import annotations

import argparse
import sys
from typing import Any


def _import_interop() -> tuple[Any, Any, Any, Any, Any] | None:
    """Import optional interop dependencies with a clear Flax error."""
    try:
        import flax  # type: ignore
        import flax.linen as _flax_linen  # noqa: F401  # type: ignore
    except ImportError as err:
        print(
            "ERROR: Haiku/Flax interop requires the optional dependency 'flax'.\n"
            "Install a compatible flax package in this Python environment, then rerun this script.",
            file=sys.stderr,
        )
        print(f"Original ImportError: {err}", file=sys.stderr)
        return None

    try:
        import haiku as hk  # type: ignore
        import haiku.experimental.flax as hkflax  # type: ignore
        import jax  # type: ignore
        import jax.numpy as jnp  # type: ignore
    except ImportError as err:
        print(
            "ERROR: Could not import Haiku, JAX, or Haiku's Flax interop module.\n"
            "Check that dm-haiku, jax, jaxlib, and flax are installed together.",
            file=sys.stderr,
        )
        print(f"Original ImportError: {err}", file=sys.stderr)
        return None

    try:
        # Access a public symbol so Haiku's no-Flax shim raises here if active.
        _ = hkflax.Module
    except ImportError as err:
        print(
            "ERROR: Haiku's Flax interop shim reports that flax is not installed.",
            file=sys.stderr,
        )
        print(f"Original ImportError: {err}", file=sys.stderr)
        return None

    return hk, hkflax, jax, jnp, flax


def _shape_dtype_tree(collection: dict[str, dict[str, Any]]) -> dict[str, dict[str, tuple[tuple[int, ...], str]]]:
    """Return a lightweight `{module: {name: (shape, dtype)}}` summary."""
    out: dict[str, dict[str, tuple[tuple[int, ...], str]]] = {}
    for module_name, leaves in collection.items():
        out[module_name] = {}
        for name, value in leaves.items():
            out[module_name][name] = (tuple(value.shape), str(value.dtype))
    return out


def module_create_smoke() -> None:
    imported = _import_interop()
    if imported is None:
        raise SystemExit(2)
    hk, hkflax, jax, jnp, flax = imported

    x = jnp.ones([2, 4], dtype=jnp.float32)
    rng = jax.random.PRNGKey(0)

    mod = hkflax.Module.create(hk.Linear, 3, name="projection")
    variables = mod.init(rng, x)
    y = mod.apply(variables, x)

    assert tuple(y.shape) == (2, 3), f"unexpected output shape: {y.shape}"

    variables_dict = flax.core.unfreeze(variables)
    collections = sorted(variables_dict)
    assert "params" in variables_dict, f"missing params collection: {collections}"

    hk_params = hkflax.flatten_flax_to_haiku(variables_dict["params"])
    summary = _shape_dtype_tree(hk_params)
    assert any("w" in leaves for leaves in hk_params.values()), summary

    print("haiku_version:", getattr(hk, "__version__", "unknown"))
    print("jax_version:", getattr(jax, "__version__", "unknown"))
    print("flax_version:", getattr(flax, "__version__", "unknown"))
    print("variables_collections:", collections)
    print("haiku_style_params:", summary)
    print("output_shape:", tuple(y.shape))
    print("OK: hk.experimental.flax.Module.create wrapped hk.Linear and applied successfully")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a small optional-dependency smoke test for Haiku/Flax interop."
    )
    parser.add_argument(
        "--mode",
        choices=("module-create",),
        default="module-create",
        help="Smoke path to run. Currently only wraps hk.Linear with Module.create.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.mode == "module-create":
        module_create_smoke()
    else:  # Defensive; argparse choices should prevent this.
        raise ValueError(f"unsupported mode: {args.mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
