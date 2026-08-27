#!/usr/bin/env python3
"""Run a tiny JAX DPM-Solver smoke sample using the bundled solver copy."""

from __future__ import annotations

import argparse
import importlib.util
import pathlib


def load_solver_module():
    root_scripts = pathlib.Path(__file__).resolve().parents[3] / "scripts"
    path = root_scripts / "dpm_solver_jax.py"
    spec = importlib.util.spec_from_file_location("skill_dpm_solver_jax", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import bundled solver from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=2)
    parser.add_argument("--order", type=int, default=1)
    parser.add_argument("--method", choices=["multistep", "singlestep", "singlestep_fixed"], default="multistep")
    parser.add_argument("--predict-x0", action="store_true")
    args = parser.parse_args()

    import jax.numpy as jnp

    mod = load_solver_module()
    ns = mod.NoiseScheduleVP(schedule="linear")
    solver = mod.DPM_Solver(lambda x, t: jnp.zeros_like(x), ns, predict_x0=args.predict_x0)
    x = jnp.ones((2, 3))
    out = solver.sample(x, steps=args.steps, order=args.order, method=args.method)
    print({"shape": tuple(out.shape), "finite": bool(jnp.isfinite(out).all()), "sum": float(out.sum())})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
