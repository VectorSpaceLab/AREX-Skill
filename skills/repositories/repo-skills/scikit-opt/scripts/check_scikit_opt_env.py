#!/usr/bin/env python3
"""Quick scikit-opt environment sanity check.

This helper is safe to run from any working directory. It imports the installed
package, prints the verified version, and can optionally probe the optional torch
and PSO_TSP caveat surfaces without depending on the original repository.
"""

from __future__ import annotations

import argparse
import inspect
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check that scikit-opt is importable and inspectable.")
    parser.add_argument("--check-torch", action="store_true", help="Also report whether torch and CUDA are available.")
    parser.add_argument("--check-route-caveat", action="store_true", help="Also report the known PSO_TSP construction caveat.")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    import sko
    from sko.GA import GA, GA_TSP
    from sko.DE import DE
    from sko.PSO import PSO
    from sko.SA import SAFast
    from sko.ACA import ACA_TSP
    from sko.IA import IA_TSP
    from sko.AFSA import AFSA
    from sko.tools import set_run_mode

    print(f"sko_version={sko.__version__}")
    for obj in [GA, GA_TSP, DE, PSO, SAFast, ACA_TSP, IA_TSP, AFSA, set_run_mode]:
        print(f"{obj.__name__}{inspect.signature(obj)}")

    if args.check_route_caveat:
        try:
            import numpy as np
            from scipy.spatial import distance
            from sko.PSO import PSO_TSP

            coords = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
            dm = distance.cdist(coords, coords)

            def route_cost(route):
                route = np.asarray(route, dtype=int)
                return float(sum(dm[route[i % len(route)], route[(i + 1) % len(route)]] for i in range(len(route))))

            PSO_TSP(func=lambda X: np.array([route_cost(r) for r in X]), n_dim=4, size_pop=8, max_iter=3)
        except TypeError as exc:
            print(f"PSO_TSP_caveat={exc}")
        else:
            print("PSO_TSP_caveat=unexpectedly_passed")

    if args.check_torch:
        try:
            import torch

            print(f"torch_version={torch.__version__}")
            print(f"torch_cuda_available={torch.cuda.is_available()}")
        except Exception as exc:  # pragma: no cover - optional surface
            print(f"torch_error={type(exc).__name__}: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
