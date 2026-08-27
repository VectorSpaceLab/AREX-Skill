#!/usr/bin/env python3
"""Report IKPy core and optional dependency availability without side effects."""
from __future__ import annotations

import argparse
import importlib
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-jax", action="store_true", help="exit non-zero if JAX is unavailable")
    parser.add_argument("--require-plot", action="store_true", help="exit non-zero if plotting dependencies are unavailable")
    args = parser.parse_args()

    try:
        import ikpy
    except Exception as exc:
        print(f"ikpy: unavailable ({type(exc).__name__}: {exc})")
        return 2

    print(f"ikpy: available (version={getattr(ikpy, '__version__', 'unknown')})")
    checks = {
        "numpy": "numpy",
        "scipy": "scipy",
        "sympy": "sympy",
        "jax": "jax",
        "jaxlib": "jaxlib",
        "matplotlib": "matplotlib",
        "graphviz-python": "graphviz",
    }
    statuses: dict[str, bool] = {}
    for label, module_name in checks.items():
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, "__version__", "available")
            print(f"{label}: available ({version})")
            statuses[label] = True
        except Exception as exc:
            print(f"{label}: unavailable ({type(exc).__name__}: {exc})")
            statuses[label] = False

    if args.require_jax and not (statuses["jax"] and statuses["jaxlib"]):
        return 1
    if args.require_plot and not (statuses["matplotlib"] and statuses["graphviz-python"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
