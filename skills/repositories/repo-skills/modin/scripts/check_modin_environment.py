#!/usr/bin/env python3
"""Check an installed Modin package and run a tiny backend smoke."""
from __future__ import annotations

import argparse
import importlib
import json
import os


def configure(engine: str, cpus: int) -> None:
    os.environ.pop("MODIN_BACKEND", None)
    os.environ.pop("MODIN_ENGINE", None)
    os.environ.pop("MODIN_STORAGE_FORMAT", None)
    if engine == "Native":
        os.environ["MODIN_BACKEND"] = "Pandas"
    else:
        os.environ["MODIN_ENGINE"] = engine
    os.environ["MODIN_CPUS"] = str(cpus)
    os.environ.setdefault("MODIN_NPARTITIONS", str(min(max(cpus, 1), 4)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", choices=("Python", "Ray", "Dask", "Native"), default="Python")
    parser.add_argument("--cpus", type=int, default=2)
    args = parser.parse_args()
    if args.cpus < 1:
        parser.error("--cpus must be positive")
    configure(args.engine, args.cpus)

    import modin
    import modin.config as cfg
    import modin.pandas as pd

    df = pd.DataFrame({"group": ["a", "a", "b"], "value": [1, 2, 3]})
    result = df.groupby("group")["value"].sum().sort_index().modin.to_pandas().to_dict()
    if result != {"a": 3, "b": 3}:
        raise RuntimeError(f"Unexpected smoke result: {result}")

    versions = {"modin": modin.__version__}
    for name in ("pandas", "numpy", "ray", "dask", "distributed"):
        try:
            module = importlib.import_module(name)
        except ImportError:
            versions[name] = "not installed"
        else:
            versions[name] = getattr(module, "__version__", "unknown")

    print(
        json.dumps(
            {
                "requested_engine": args.engine,
                "active_engine": cfg.Engine.get(),
                "backend": cfg.Backend.get(),
                "storage_format": cfg.StorageFormat.get(),
                "npartitions": cfg.NPartitions.get(),
                "result": result,
                "versions": versions,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
