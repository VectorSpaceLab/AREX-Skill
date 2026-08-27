#!/usr/bin/env python3
"""Run a tiny, deterministic smoke check for h3-py's public API variants.

This diagnostic intentionally avoids benchmarks and geospatial workflow claims.
It reports imports, public signatures, scalar representations, collection
representations, and cross-variant value parity.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import sys
from collections.abc import Iterable

SEED_HEX = "8928308280fffff"
LATITUDE = 37.7752702151959
LONGITUDE = -122.418307270836
RESOLUTION = 9


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Smoke-check h3's basic_str, basic_int, memview_int, and optional "
            "numpy_int API variants. No benchmark or network access is used."
        )
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="print only failures and the final status",
    )
    return parser.parse_args()


def _typename(value: object) -> str:
    return type(value).__name__


def _dtype(value: object) -> str:
    dtype = getattr(value, "dtype", None)
    return str(dtype) if dtype is not None else "-"


def _as_hex(api: object, value: object) -> str:
    if isinstance(value, str):
        return value
    return api.int_to_str(int(value))


def _collection_as_hex(api: object, values: Iterable[object]) -> list[str]:
    return [_as_hex(api, value) for value in values]


def _report(message: str, quiet: bool = False) -> None:
    if not quiet:
        print(message)


def _is_memoryview_result(value: object) -> bool:
    """Check the buffer contract without depending on Cython internals."""
    try:
        view = memoryview(value)
    except TypeError:
        return False
    return view.itemsize == 8 and view.format in {"Q", "L"}


def main() -> int:
    args = _parse_args()
    quiet = args.quiet
    failures: list[str] = []
    loaded: dict[str, object] = {}

    module_names = {
        "basic_str": "h3.api.basic_str",
        "basic_int": "h3.api.basic_int",
        "memview_int": "h3.api.memview_int",
        "numpy_int": "h3.api.numpy_int",
    }

    numpy_available = True
    try:
        importlib.import_module("numpy")
    except ImportError:
        numpy_available = False

    for name, module_name in module_names.items():
        try:
            loaded[name] = importlib.import_module(module_name)
            _report(f"[ok] import {module_name}", quiet)
        except ImportError as exc:
            if name == "numpy_int" and not numpy_available:
                _report(
                    '[skip] numpy_int: NumPy is not installed. '
                    'Install the optional dependency with '
                    'python -m pip install "h3[numpy]", or use basic_int '
                    'or memview_int.',
                    quiet=False,
                )
            else:
                failures.append(f"import {module_name}: {type(exc).__name__}: {exc}")
                _report(f"[FAIL] {failures[-1]}", quiet=False)
        except Exception as exc:  # pragma: no cover - defensive diagnostic path
            failures.append(f"import {module_name}: {type(exc).__name__}: {exc}")
            _report(f"[FAIL] {failures[-1]}", quiet=False)

    required = {"basic_str", "basic_int", "memview_int"}
    if not required.issubset(loaded):
        failures.append("one or more dependency-free API variants could not import")
        print("[FAIL] dependency-free API set is incomplete")
        return 1

    canonical: dict[str, set[str]] = {}
    for name, api in loaded.items():
        try:
            signatures = ", ".join(
                f"{fn}{inspect.signature(getattr(api, fn))}"
                for fn in ("latlng_to_cell", "grid_ring", "int_to_str", "str_to_int")
            )
            _report(f"[ok] {name} signatures: {signatures}", quiet)

            scalar = api.latlng_to_cell(LATITUDE, LONGITUDE, RESOLUTION)
            scalar_hex = _as_hex(api, scalar)
            round_trip = api.str_to_int(api.int_to_str(int(api.str_to_int(scalar_hex))))
            if int(round_trip) != int(api.str_to_int(scalar_hex)):
                raise AssertionError("int_to_str/str_to_int did not round-trip")

            collection = api.grid_ring(scalar, 1)
            values = _collection_as_hex(api, collection)
            if not values:
                raise AssertionError("tiny grid_ring returned no values")
            canonical[name] = set(values)

            _report(
                f"[ok] {name}: scalar={scalar!r} ({_typename(scalar)}), "
                f"collection={_typename(collection)}, dtype={_dtype(collection)}, "
                f"count={len(values)}, scalar_hex={scalar_hex}",
                quiet,
            )

            if name == "memview_int":
                if not _is_memoryview_result(collection):
                    raise AssertionError("collection is not an unsigned 64-bit buffer")
                view = memoryview(collection)
                _report(
                    f"[ok] memview buffer: format={view.format!r}, "
                    f"itemsize={view.itemsize}, readonly={view.readonly}",
                    quiet,
                )
            if name == "numpy_int":
                if not numpy_available:
                    raise AssertionError("NumPy route was imported but NumPy is unavailable")
                if _dtype(collection) != "uint64":
                    raise AssertionError(f"expected uint64 dtype, got {_dtype(collection)!r}")
        except ModuleNotFoundError as exc:
            if name == "numpy_int" and not numpy_available:
                _report(
                    '[skip] numpy_int operation: NumPy is not installed. '
                    'Install "h3[numpy]" to enable ndarray output.',
                    quiet=False,
                )
            else:
                failures.append(f"{name} operation: {type(exc).__name__}: {exc}")
                _report(f"[FAIL] {failures[-1]}", quiet=False)
        except Exception as exc:
            failures.append(f"{name} operation: {type(exc).__name__}: {exc}")
            _report(f"[FAIL] {failures[-1]}", quiet=False)

    baseline = canonical.get("basic_str")
    if baseline is not None:
        for name, values in canonical.items():
            if values != baseline:
                failures.append(f"{name} does not match basic_str after hex normalization")
                _report(f"[FAIL] {failures[-1]}", quiet=False)
        if not failures:
            _report("[ok] cross-API collection parity after hex normalization", quiet)

    if failures:
        print(f"STATUS: FAIL ({len(failures)} issue(s))")
        return 1
    print("STATUS: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
