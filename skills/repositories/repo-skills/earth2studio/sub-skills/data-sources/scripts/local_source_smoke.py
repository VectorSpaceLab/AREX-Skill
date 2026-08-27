#!/usr/bin/env python3
"""Validate a small local Earth2Studio-compatible data fixture.

The default self-test uses an in-memory xarray DataArray and the package's
local source adapters. ``--path`` is optional and may point to a NetCDF/Zarr
fixture; this helper never downloads data or contacts remote stores.
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np
import xarray as xr


def _fixture() -> xr.DataArray:
    return xr.DataArray(
        np.arange(8, dtype=np.float32).reshape(2, 2, 2),
        dims=("time", "lat", "lon"),
        coords={
            "time": np.array(["2024-01-01T00:00:00", "2024-01-01T01:00:00"], dtype="datetime64[ns]"),
            "lat": np.array([0.0, 1.0]),
            "lon": np.array([10.0, 11.0]),
        },
        name="t2m",
    )


def _check_array(array: xr.DataArray, variable: str) -> dict[str, object]:
    if "time" not in array.dims:
        raise ValueError("fixture must contain a time dimension")
    if variable and array.name not in {None, variable}:
        raise ValueError(f"requested variable {variable!r} does not match {array.name!r}")
    for dim in ("lat", "lon"):
        if dim not in array.coords:
            raise ValueError(f"fixture is missing {dim!r} coordinates")
    return {"name": array.name, "dims": list(array.dims), "shape": list(array.shape)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, help="Optional local NetCDF or Zarr fixture")
    parser.add_argument("--time", help="Optional ISO time to validate against the fixture")
    parser.add_argument("--variable", default="t2m")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.path is None:
        array = _fixture()
        source = "in-memory fixture"
    else:
        if not args.path.exists():
            parser.error(f"local path does not exist: {args.path}")
        dataset = xr.open_zarr(args.path) if args.path.is_dir() else xr.open_dataset(args.path)
        if args.variable not in dataset:
            raise ValueError(f"dataset has no variable {args.variable!r}")
        array = dataset[args.variable]
        source = str(args.path)
    if args.time is not None and np.datetime64(args.time) not in array.time.values:
        raise ValueError(f"time {args.time!r} is not present")
    result = _check_array(array, args.variable)
    result["source"] = source
    result["offline"] = True
    if args.json:
        import json
        print(json.dumps(result, sort_keys=True, default=str))
    else:
        print("local source smoke: PASS")
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
