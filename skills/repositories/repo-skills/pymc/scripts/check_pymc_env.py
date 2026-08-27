#!/usr/bin/env python3
"""Check a PyMC installation and optional backend modules."""
from __future__ import annotations

import argparse
import importlib
import json
import math
from importlib.metadata import PackageNotFoundError, version
from typing import Any

OPTIONAL_MODULES = ("nutpie", "jax", "jaxlib", "numpyro", "blackjax", "zarr", "mcbackend", "graphviz")


def package_version(dist: str) -> str | None:
    try:
        return version(dist)
    except PackageNotFoundError:
        return None


def optional_status() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for name in OPTIONAL_MODULES:
        entry: dict[str, Any] = {"importable": False, "version": package_version(name)}
        try:
            module = importlib.import_module(name)
        except Exception as exc:
            entry["error"] = f"{type(exc).__name__}: {exc}"
        else:
            entry["importable"] = True
            entry["module_version"] = getattr(module, "__version__", None)
            if name == "jax":
                try:
                    entry["devices"] = [str(device) for device in module.devices()]
                except Exception as exc:
                    entry["devices_error"] = f"{type(exc).__name__}: {exc}"
        out[name] = entry
    return out


def smoke(seed: int) -> dict[str, Any]:
    import numpy as np
    import pymc as pm

    with pm.Model(coords={"obs": range(4)}) as model:
        x = pm.Data("x", np.linspace(-1, 1, 4), dims="obs")
        a = pm.Normal("a", 0, 1)
        b = pm.Normal("b", 0, 1)
        mu = pm.Deterministic("mu", a + b * x, dims="obs")
        pm.Normal("y", mu=mu, sigma=0.5, observed=[-1, -0.2, 0.2, 1], dims="obs")
        point = model.initial_point(random_seed=seed)
        logp = float(model.compile_logp()(point))
        assert math.isfinite(logp)
        prior = pm.sample_prior_predictive(draws=2, random_seed=seed, return_inferencedata=True)
    return {
        "initial_logp": logp,
        "initial_point_keys": sorted(point),
        "prior_groups": sorted(str(key) for key in getattr(prior, "children", {})),
        "model_variables": sorted(model.named_vars),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check PyMC importability, versions, optional backends, and an optional tiny smoke.")
    parser.add_argument("--run-smoke", action="store_true", help="Run a tiny CPU model, logp, and prior predictive smoke.")
    parser.add_argument("--seed", type=int, default=20260812)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    args = parser.parse_args(argv)

    result: dict[str, Any] = {"ok": False, "packages": {}, "optional_modules": {}}
    try:
        import pymc as pm
        import pytensor
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        print(json.dumps(result, indent=2) if args.json else result["error"])
        return 1

    result["packages"] = {
        "pymc": getattr(pm, "__version__", package_version("pymc")),
        "pytensor": getattr(pytensor, "__version__", package_version("pytensor")),
    }
    result["optional_modules"] = optional_status()
    if args.run_smoke:
        result["smoke"] = smoke(args.seed)
    result["ok"] = True

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("PyMC environment check: OK")
        print("  pymc:", result["packages"]["pymc"])
        print("  pytensor:", result["packages"]["pytensor"])
        for name, entry in result["optional_modules"].items():
            print(f"  optional {name}: {'yes' if entry['importable'] else 'no'}")
        if args.run_smoke:
            print("  tiny smoke: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
