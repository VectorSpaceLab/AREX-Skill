#!/usr/bin/env python3
"""Check a Python environment for dm-haiku, JAX, and optional Flax interop.

The script performs only safe local imports and tiny synthetic array operations.
It does not download data, read a source checkout, train, or require a GPU.

Examples:
  python check_haiku_env.py
  python check_haiku_env.py --require-flax
  python check_haiku_env.py --require-accelerator
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib import metadata
from typing import Any


def _version(dist: str) -> str | None:
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return None


def _device_summary(jax_module: Any) -> list[str]:
    try:
        return [str(device) for device in jax_module.devices()]
    except Exception as exc:  # pragma: no cover - diagnostic fallback
        return [f"<device query failed: {type(exc).__name__}: {exc}>"]


def run(require_flax: bool, require_accelerator: bool) -> dict[str, Any]:
    try:
        import haiku as hk
        import jax
        import jax.numpy as jnp
    except Exception as exc:
        raise RuntimeError(
            "Failed to import haiku/JAX. Install a compatible JAX backend first, "
            "then install dm-haiku in the same Python environment."
        ) from exc

    def forward(x):
        return hk.Linear(2, name="env_probe_linear")(x)

    transformed = hk.without_apply_rng(hk.transform(forward))
    x = jnp.ones([1, 3], dtype=jnp.float32)
    params = transformed.init(jax.random.PRNGKey(0), x)
    y = transformed.apply(params, x)
    if tuple(y.shape) != (1, 2):
        raise AssertionError(f"Haiku Linear smoke produced shape {tuple(y.shape)}")

    backend = jax.default_backend()
    devices = _device_summary(jax)
    if require_accelerator and backend == "cpu":
        raise RuntimeError(
            "JAX default backend is CPU. Install and verify an accelerator-enabled "
            "JAX backend before claiming GPU/TPU execution."
        )

    flax_status: dict[str, Any] = {"checked": False, "available": None}
    if require_flax:
        try:
            flax = importlib.import_module("flax")
            import haiku.experimental.flax as hkflax
            mod = hkflax.Module.create(hk.Linear, 2)
            variables = mod.init(jax.random.PRNGKey(1), x)
            out = mod.apply(variables, x)
            if tuple(out.shape) != (1, 2):
                raise AssertionError(f"Flax interop smoke produced shape {tuple(out.shape)}")
            flax_status = {
                "checked": True,
                "available": True,
                "version": getattr(flax, "__version__", _version("flax")),
                "collections": sorted(variables.keys()),
            }
        except Exception as exc:
            raise RuntimeError(
                "Flax interop check failed. Install a compatible flax package or "
                "avoid haiku.experimental.flax workflows."
            ) from exc

    return {
        "ok": True,
        "python": sys.version.split()[0],
        "versions": {
            "dm-haiku": _version("dm-haiku"),
            "haiku.__version__": getattr(hk, "__version__", None),
            "jax": getattr(jax, "__version__", _version("jax")),
            "jaxlib": _version("jaxlib"),
            "flax": _version("flax"),
        },
        "jax_backend": backend,
        "jax_devices": devices,
        "haiku_smoke": {
            "output_shape": list(y.shape),
            "param_modules": sorted(params.keys()),
        },
        "flax": flax_status,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-flax", action="store_true", help="Also verify optional haiku.experimental.flax interop.")
    parser.add_argument("--require-accelerator", action="store_true", help="Fail if JAX reports CPU as the default backend.")
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.require_flax, args.require_accelerator), indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"check_haiku_env: FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
