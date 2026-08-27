#!/usr/bin/env python3
"""Check an installed NumPyro/JAX environment.

The script verifies core imports, reports JAX backend/device facts, performs a
tiny distribution smoke, and optionally probes common NumPyro optional
dependencies. Missing optional dependencies do not fail unless explicitly
required.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
import sys
from typing import Any

OPTIONAL_GROUPS = {
    "funsor": ["funsor", "numpyro.contrib.funsor"],
    "optax": ["optax"],
    "flax": ["flax", "numpyro.contrib.module"],
    "equinox": ["equinox", "numpyro.contrib.module"],
    "hsgp": [
        "numpyro.contrib.hsgp.approximation",
        "numpyro.contrib.hsgp.laplacian",
        "numpyro.contrib.hsgp.spectral_densities",
    ],
    "tfp": ["tensorflow_probability.substrates.jax", "numpyro.contrib.tfp.distributions"],
    "jaxns": ["jaxns", "numpyro.contrib.nested_sampling"],
    "graphviz": ["graphviz"],
    "plotting-data": ["matplotlib", "pandas", "sklearn"],
}


def clean_message(exc: BaseException) -> str:
    text = str(exc).splitlines()[0] if str(exc) else exc.__class__.__name__
    for value in [os.getcwd(), str(Path.home()), sys.prefix, sys.executable]:
        if value and value not in {"/", "."}:
            text = text.replace(value, "<local-path>")
    return text


def import_status(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        return {"module": module_name, "status": "missing", "error": clean_message(exc)}
    except Exception as exc:
        return {"module": module_name, "status": "error", "error": clean_message(exc)}
    version = getattr(module, "__version__", None)
    return {"module": module_name, "status": "ok", "version": version}


def run(args: argparse.Namespace) -> int:
    result: dict[str, Any] = {"core": {}, "optional": {}, "failures": []}
    try:
        import jax
        import jax.numpy as jnp
        from jax import random
        import numpyro
        import numpyro.distributions as dist
    except Exception as exc:
        result["failures"].append({"phase": "core import", "error": clean_message(exc)})
        print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
        return 1

    if args.platform:
        numpyro.set_platform(args.platform)
    if args.host_device_count:
        numpyro.set_host_device_count(args.host_device_count)
    if args.x64:
        numpyro.enable_x64()

    try:
        x = dist.Normal(0.0, 1.0).sample(random.key(args.seed), sample_shape=(3,))
        finite = bool(jnp.isfinite(dist.Normal(0.0, 1.0).log_prob(x)).all())
        assert finite
        result["core"] = {
            "numpyro_version": getattr(numpyro, "__version__", None),
            "jax_version": getattr(jax, "__version__", None),
            "jax_backend": jax.default_backend(),
            "devices": [str(device) for device in jax.devices()],
            "local_device_count": jax.local_device_count(),
            "normal_sample_shape": tuple(x.shape),
            "finite_log_prob": finite,
            "x64_requested": bool(args.x64),
        }
    except Exception as exc:
        result["failures"].append({"phase": "core smoke", "error": clean_message(exc)})

    selected = args.optional if args.optional else []
    if "all" in selected:
        selected = sorted(OPTIONAL_GROUPS)
    for group in selected:
        modules = OPTIONAL_GROUPS.get(group)
        if modules is None:
            result["optional"][group] = {"status": "unknown-group", "imports": []}
            continue
        imports = [import_status(module_name) for module_name in modules]
        statuses = {item["status"] for item in imports}
        status = "error" if "error" in statuses else "missing" if "missing" in statuses else "ok"
        result["optional"][group] = {"status": status, "imports": imports}

    required = args.require or []
    if "all" in required:
        required = sorted(OPTIONAL_GROUPS)
    for group in required:
        if group not in result["optional"]:
            modules = OPTIONAL_GROUPS.get(group, [])
            imports = [import_status(module_name) for module_name in modules]
            statuses = {item["status"] for item in imports}
            status = "error" if "error" in statuses else "missing" if "missing" in statuses else "ok"
            result["optional"][group] = {"status": status, "imports": imports}
        if result["optional"].get(group, {}).get("status") != "ok":
            result["failures"].append({"phase": "required optional dependency", "group": group, "status": result["optional"].get(group, {}).get("status")})

    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if not result["failures"] else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Check NumPyro, JAX backend, and optional dependency availability.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--platform", choices=["cpu", "gpu", "tpu"], default=None)
    parser.add_argument("--host-device-count", type=int, default=0)
    parser.add_argument("--x64", action="store_true")
    parser.add_argument("--optional", nargs="*", default=[], help="Optional groups to probe, or 'all'.")
    parser.add_argument("--require", nargs="*", default=[], help="Optional groups that must be available, or 'all'.")
    parser.add_argument("--list-optional", action="store_true", help="List optional group names and exit.")
    args = parser.parse_args()
    if args.list_optional:
        print("\n".join(sorted(OPTIONAL_GROUPS)))
        raise SystemExit(0)
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
