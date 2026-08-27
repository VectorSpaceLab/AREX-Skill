#!/usr/bin/env python3
"""Report optional Ludwig AutoML/HPO dependencies without running a search."""
import importlib.util
import json

PACKAGES = ["ludwig", "dask", "ray", "optuna", "hyperopt", "ConfigSpace", "ax", "nevergrad", "skopt"]


def main() -> int:
    result = {name: bool(importlib.util.find_spec(name)) for name in PACKAGES}
    advice = []
    if not result.get("ray"):
        advice.append("Ray is missing; Ray backend, Ray Tune, and distributed HPO need distributed dependencies.")
    if not result.get("optuna"):
        advice.append("Optuna is missing; native Optuna executor configs need optuna installed.")
    if not result.get("dask"):
        advice.append("Dask is missing; AutoML/dataframe paths may fail to import.")
    print(json.dumps({"packages": result, "advice": advice}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
