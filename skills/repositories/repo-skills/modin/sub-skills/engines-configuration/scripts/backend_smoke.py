#!/usr/bin/env python3
"""Run a tiny Modin backend smoke test."""

from __future__ import annotations

import argparse
import json
import os
from typing import Any

ENGINE_CHOICES = ("Ray", "Dask", "Python", "Native")


def _configure_environment(engine: str, cpus: int | None) -> None:
    """Populate environment settings before Modin imports configuration."""
    for key in ("MODIN_BACKEND", "MODIN_ENGINE", "MODIN_STORAGE_FORMAT"):
        os.environ.pop(key, None)

    if engine == "Native":
        os.environ["MODIN_BACKEND"] = "Pandas"
    else:
        os.environ["MODIN_ENGINE"] = engine
    if cpus is not None:
        os.environ["MODIN_CPUS"] = str(cpus)


def run_smoke(engine: str, cpus: int | None, include_versions: bool) -> dict[str, Any]:
    """Run a deterministic tiny DataFrame operation and return a report."""
    _configure_environment(engine, cpus)

    import modin
    import modin.config as cfg
    import modin.pandas as pd

    df = pd.DataFrame(
        {
            "group": ["a", "a", "b", "b"],
            "value": [1, 2, 10, 20],
        }
    )
    grouped = df.groupby("group")["value"].sum().sort_index()
    result_series = grouped.modin.to_pandas()
    result = {str(key): int(value) for key, value in result_series.to_dict().items()}
    expected = {"a": 3, "b": 30}
    if result != expected:
        raise RuntimeError(f"Unexpected smoke result: {result}; expected {expected}")

    report: dict[str, Any] = {
        "requested_engine": engine,
        "active_engine": cfg.Engine.get(),
        "storage_format": cfg.StorageFormat.get(),
        "global_backend": cfg.Backend.get(),
        "dataframe_backend": df.get_backend(),
        "npartitions": cfg.NPartitions.get(),
        "result": result,
    }
    if include_versions:
        versions: dict[str, str] = {"modin": modin.__version__}
        for package in ("pandas", "numpy", "ray", "dask", "distributed"):
            try:
                module = __import__(package)
            except ImportError:
                versions[package] = "not installed"
            else:
                versions[package] = getattr(module, "__version__", "unknown")
        report["versions"] = versions
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Smoke-test Modin with a tiny DataFrame operation under Ray, Dask, "
            "Python, or Native/Pandas execution. Put distributed work under this "
            "script's main guard to avoid multiprocessing import errors."
        )
    )
    parser.add_argument(
        "--engine",
        choices=ENGINE_CHOICES,
        default="Python",
        help="Execution engine to request before importing modin.pandas.",
    )
    parser.add_argument(
        "--cpus",
        type=int,
        default=None,
        help="Optional MODIN_CPUS value to set before Modin starts the engine.",
    )
    parser.add_argument(
        "--versions",
        action="store_true",
        help="Include installed package versions in the JSON report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.cpus is not None and args.cpus <= 0:
        raise SystemExit("--cpus must be a positive integer when provided")
    report = run_smoke(args.engine, args.cpus, args.versions)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
