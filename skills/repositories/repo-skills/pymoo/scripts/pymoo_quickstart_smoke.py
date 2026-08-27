#!/usr/bin/env python3
"""Root-level pymoo quickstart smoke.

Checks package version, compiled-extension availability, and a tiny NSGA-II run
on the built-in ZDT1 problem. Safe for CPU-only environments.
"""

from __future__ import annotations

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a small pymoo install/API smoke test.")
    parser.add_argument("--pop-size", type=int, default=20, help="Small NSGA-II population size.")
    parser.add_argument("--n-gen", type=int, default=3, help="Small generation budget.")
    parser.add_argument("--seed", type=int, default=1, help="Random seed.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    args = parser.parse_args()

    import pymoo
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.functions import is_compiled
    from pymoo.optimize import minimize
    from pymoo.problems import get_problem

    res = minimize(get_problem("zdt1"), NSGA2(pop_size=args.pop_size), ("n_gen", args.n_gen), seed=args.seed, verbose=False)

    assert res.F is not None and res.F.ndim == 2 and res.F.shape[1] == 2, f"unexpected F shape: {None if res.F is None else res.F.shape}"
    assert res.X is not None and res.X.shape[0] == res.F.shape[0], "X/F rows are not aligned"
    assert res.algorithm.evaluator.n_eval > 0, "no evaluations were counted"

    payload = {
        "pymoo_version": getattr(pymoo, "__version__", "unknown"),
        "compiled_extensions": bool(is_compiled()),
        "F_shape": list(res.F.shape),
        "X_shape": list(res.X.shape),
        "evaluations": int(res.algorithm.evaluator.n_eval),
        "generations": int(res.algorithm.n_gen),
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("pymoo quickstart smoke passed")
        for key, value in payload.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
