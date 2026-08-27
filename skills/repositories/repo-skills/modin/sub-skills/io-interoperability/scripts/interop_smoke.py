#!/usr/bin/env python3
"""Run tiny Modin interoperability conversion smoke checks."""
from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from typing import Callable


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--engine",
        choices=("Python", "Ray", "Dask", "Unidist", "Auto"),
        default="Auto",
        help="Set MODIN_ENGINE before importing Modin. Auto leaves an existing setting unchanged or uses Python.",
    )
    parser.add_argument("--cpus", type=int, default=2, help="Set MODIN_CPUS for this process.")
    parser.add_argument(
        "--arrow",
        choices=("auto", "on", "off"),
        default="auto",
        help="Check Arrow conversion. 'auto' skips if pyarrow is not installed.",
    )
    parser.add_argument("--check-ray", action="store_true", help="Also check Modin <-> Ray Dataset conversion. Requires Ray engine and Ray Data.")
    parser.add_argument("--check-dask", action="store_true", help="Also check Modin <-> Dask DataFrame conversion. Requires Dask engine and dask.dataframe.")
    parser.add_argument("--strict-optional", action="store_true", help="Fail optional Arrow/Ray/Dask checks instead of reporting them as skipped.")
    return parser.parse_args(argv)


def configure_environment(engine: str, cpus: int) -> str:
    if cpus <= 0:
        raise ValueError("--cpus must be positive")
    os.environ.pop("MODIN_BACKEND", None)
    os.environ.pop("MODIN_STORAGE_FORMAT", None)
    selected = os.environ.get("MODIN_ENGINE") if engine == "Auto" else engine
    if not selected:
        selected = "Python"
    os.environ["MODIN_ENGINE"] = selected
    os.environ["MODIN_CPUS"] = str(cpus)
    os.environ.setdefault("MODIN_NPARTITIONS", str(min(max(cpus, 1), 4)))
    return selected


def require_or_report(name: str, check: Callable[[], None], strict: bool) -> str:
    try:
        check()
    except Exception as exc:
        if strict:
            raise
        return f"{name} skipped/failed optional check: {type(exc).__name__}: {exc}"
    return f"{name} ok"


def assert_frame_equal(actual, expected, *, check_dtype: bool = True) -> None:
    import pandas as pandas_pd

    pandas_pd.testing.assert_frame_equal(
        actual.reset_index(drop=True), expected.reset_index(drop=True), check_dtype=check_dtype
    )


def run_required_checks() -> tuple[object, object, list[str]]:
    import numpy as numpy_np
    import pandas as pandas_pd
    import modin.pandas as pd
    from modin.pandas.io import from_dataframe

    expected = pandas_pd.DataFrame(
        {
            "id": [1, 2, 3],
            "group": ["a", "a", "b"],
            "value": [10.0, 20.5, 30.0],
        }
    )
    modin_df = pd.DataFrame(expected)

    assert_frame_equal(modin_df.modin.to_pandas(), expected)
    messages = ["pandas round-trip ok"]

    numpy_result = modin_df.to_numpy()
    if hasattr(numpy_result, "_to_numpy"):
        numpy_result = numpy_result._to_numpy()
    numpy_np.testing.assert_array_equal(numpy_result, expected.to_numpy())
    messages.append("numpy conversion ok")

    interchange_df = from_dataframe(modin_df.__dataframe__())
    assert_frame_equal(interchange_df.modin.to_pandas(), expected, check_dtype=False)
    messages.append("dataframe interchange ok")
    return expected, modin_df, messages


def arrow_check(expected) -> None:
    if importlib.util.find_spec("pyarrow") is None:
        raise RuntimeError("pyarrow is not installed")
    import pyarrow as pa
    from modin.pandas.io import from_arrow

    arrow_df = from_arrow(pa.Table.from_pandas(expected))
    assert_frame_equal(arrow_df.modin.to_pandas(), expected, check_dtype=False)


def ray_check(expected, modin_df, selected_engine: str, cpus: int) -> None:
    if selected_engine != "Ray":
        raise RuntimeError(f"Ray conversion requires MODIN_ENGINE=Ray, got {selected_engine!r}")
    if importlib.util.find_spec("ray") is None:
        raise RuntimeError("ray is not installed")
    import ray
    from modin.pandas.io import from_ray

    if not ray.is_initialized():
        ray.init(num_cpus=cpus, include_dashboard=False, ignore_reinit_error=True, log_to_driver=False)
    from_ray_df = from_ray(ray.data.from_pandas(expected))
    assert_frame_equal(from_ray_df.modin.to_pandas(), expected, check_dtype=False)
    ray_dataset = modin_df.modin.to_ray()
    assert_frame_equal(ray_dataset.to_pandas(), expected, check_dtype=False)


def dask_check(expected, modin_df, selected_engine: str) -> None:
    if selected_engine != "Dask":
        raise RuntimeError(f"Dask conversion requires MODIN_ENGINE=Dask, got {selected_engine!r}")
    if importlib.util.find_spec("dask.dataframe") is None:
        raise RuntimeError("dask.dataframe is not installed")
    import dask.dataframe as dd
    from modin.pandas.io import from_dask

    dask_df = dd.from_pandas(expected, npartitions=2)
    from_dask_df = from_dask(dask_df)
    assert_frame_equal(from_dask_df.modin.to_pandas(), expected, check_dtype=False)
    assert_frame_equal(modin_df.modin.to_dask().compute(), expected, check_dtype=False)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        selected_engine = configure_environment(args.engine, args.cpus)
        expected, modin_df, messages = run_required_checks()

        if args.arrow != "off":
            if args.arrow == "auto" and importlib.util.find_spec("pyarrow") is None:
                messages.append("arrow skipped: pyarrow is not installed")
            else:
                messages.append(require_or_report("arrow conversion", lambda: arrow_check(expected), args.strict_optional or args.arrow == "on"))
        if args.check_ray:
            messages.append(require_or_report("ray conversion", lambda: ray_check(expected, modin_df, selected_engine, args.cpus), args.strict_optional))
        if args.check_dask:
            messages.append(require_or_report("dask conversion", lambda: dask_check(expected, modin_df, selected_engine), args.strict_optional))
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"MODIN_ENGINE={selected_engine}")
    for message in messages:
        print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
