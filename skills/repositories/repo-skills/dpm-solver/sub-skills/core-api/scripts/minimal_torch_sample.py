#!/usr/bin/env python3
"""Run a tiny PyTorch DPM-Solver smoke sample using the bundled solver copy."""

from __future__ import annotations

import argparse
import importlib.util
import pathlib
import sys


def load_solver_module():
    root_scripts = pathlib.Path(__file__).resolve().parents[3] / "scripts"
    path = root_scripts / "dpm_solver_pytorch.py"
    spec = importlib.util.spec_from_file_location("skill_dpm_solver_pytorch", path)
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
    parser.add_argument("--algorithm-type", choices=["dpmsolver", "dpmsolver++"], default="dpmsolver")
    args = parser.parse_args()

    import torch

    mod = load_solver_module()
    ns = mod.NoiseScheduleVP(schedule="linear")
    solver = mod.DPM_Solver(lambda x, t: torch.zeros_like(x), ns, algorithm_type=args.algorithm_type)
    x = torch.ones(2, 3)
    out = solver.sample(x, steps=args.steps, order=args.order, method=args.method)
    print({"shape": tuple(out.shape), "finite": bool(torch.isfinite(out).all()), "sum": float(out.sum())})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
