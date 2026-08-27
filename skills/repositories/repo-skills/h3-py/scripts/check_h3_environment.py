#!/usr/bin/env python3
"""Run a small, safe installation and public-API smoke check for h3-py.

The helper does not download data, require a checkout, or mutate the
environment. Use --include-numpy only when the optional NumPy API is part of
the caller's contract.
"""

from __future__ import annotations

import argparse
import importlib
import sys


def check(include_numpy: bool) -> None:
    try:
        import h3
    except ImportError as exc:
        raise SystemExit(
            "h3 is not importable from this Python; install with "
            "python -m pip install h3 and retry"
        ) from exc

    versions = h3.versions()
    if not isinstance(versions, dict) or not {"python", "c"} <= versions.keys():
        raise AssertionError(f"unexpected h3.versions() result: {versions!r}")

    cell = h3.latlng_to_cell(37.769377, -122.388903, 9)
    assert h3.is_valid_cell(cell), cell
    assert h3.get_resolution(cell) == 9
    assert len(h3.grid_ring(cell, 1)) == 6

    for module_name in (
        "h3.api.basic_str",
        "h3.api.basic_int",
        "h3.api.memview_int",
    ):
        importlib.import_module(module_name)

    if include_numpy:
        try:
            import numpy as np
            import h3.api.numpy_int as numpy_api
        except ImportError as exc:
            raise SystemExit(
                "NumPy API requested but NumPy is unavailable; install with "
                "python -m pip install 'h3[numpy]'"
            ) from exc
        integer_cell = numpy_api.latlng_to_cell(0, 0, 0)
        values = numpy_api.grid_ring(integer_cell, 1)
        assert values.dtype == np.uint64, values.dtype
        assert values.shape == (5,), values.shape

    print(f"h3 smoke checks passed: python={versions['python']} c={versions['c']}")
    print(f"default cell: {cell}")
    if include_numpy:
        print("NumPy API: available and returned uint64 ndarray")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        nargs="?",
        choices=("check",),
        default="check",
        help="run deterministic import and API assertions (default: check)",
    )
    parser.add_argument(
        "--include-numpy",
        action="store_true",
        help="also import h3.api.numpy_int and check its uint64 output",
    )
    args = parser.parse_args(argv)
    check(args.include_numpy)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
