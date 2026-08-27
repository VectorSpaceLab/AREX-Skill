#!/usr/bin/env python3
"""Deterministic NumPy smoke checks for einops.einsum.

The cases are adapted from public einops einsum behavior: named multi-letter
axes, tensors-first call order, ellipsis, repeated-axis traces, attention-style
dot products, and expected unsupported syntax errors. The script depends only on
NumPy and an installed einops package.
"""

from __future__ import annotations

import argparse
import sys
from typing import Callable, Iterable


def _import_runtime():
    try:
        import numpy as np  # type: ignore
        from einops import einsum  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover - environment dependent
        missing = exc.name or "required package"
        print(
            f"Missing dependency {missing!r}. Install NumPy and einops, then rerun this script.",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    return np, einsum


def _expect_error(fn: Callable[[], object], fragments: Iterable[str], label: str) -> None:
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 - smoke script checks public error text
        message = str(exc)
        missing = [fragment for fragment in fragments if fragment not in message]
        if missing:
            raise AssertionError(
                f"{label}: expected fragments {missing!r} in {type(exc).__name__}: {message!r}"
            ) from exc
        return
    raise AssertionError(f"{label}: expected an exception")


def case_basic(verbose: bool = False) -> None:
    np, einsum = _import_runtime()
    rng = np.random.default_rng(0)
    x = rng.normal(size=(2, 3, 4, 5)).astype("float32")
    y = rng.normal(size=(2, 5)).astype("float32")
    got = einsum(x, y, "batch channel height width, batch width -> batch height")
    expected = np.einsum("bchw,bw->bh", x, y)
    assert got.shape == (2, 4)
    np.testing.assert_allclose(got, expected, rtol=1e-6, atol=1e-6)
    if verbose:
        print("basic named contraction ok", got.shape)


def case_attention(verbose: bool = False) -> None:
    np, einsum = _import_runtime()
    rng = np.random.default_rng(1)
    q = rng.normal(size=(2, 3, 4, 5)).astype("float32")
    k = rng.normal(size=(2, 6, 4, 5)).astype("float32")
    got = einsum(
        q,
        k,
        "batch query head channel, batch key head channel -> batch head query key",
    )
    expected = np.einsum("bqhc,bkhc->bhqk", q, k)
    assert got.shape == (2, 4, 3, 6)
    np.testing.assert_allclose(got, expected, rtol=1e-6, atol=1e-6)
    if verbose:
        print("attention score contraction ok", got.shape)


def case_ellipsis(verbose: bool = False) -> None:
    np, einsum = _import_runtime()
    rng = np.random.default_rng(2)
    weights = rng.normal(size=(7, 5)).astype("float32")
    data = rng.normal(size=(2, 3, 4, 5)).astype("float32")
    got = einsum(weights, data, "out_dim in_dim, ... in_dim -> ... out_dim")
    expected = np.einsum("oi,...i->...o", weights, data)
    assert got.shape == (2, 3, 4, 7)
    np.testing.assert_allclose(got, expected, rtol=1e-6, atol=1e-6)
    if verbose:
        print("ellipsis projection ok", got.shape)


def case_repeated_axes(verbose: bool = False) -> None:
    np, einsum = _import_runtime()
    matrix = np.arange(25, dtype="float32").reshape(5, 5)
    trace = einsum(matrix, "row row ->")
    np.testing.assert_allclose(trace, np.trace(matrix))

    x = np.arange(5 * 2 * 3 * 5, dtype="float32").reshape(5, 2, 3, 5)
    got = einsum(x, "token ... token -> ...")
    expected = np.einsum("a...a->...", x)
    assert got.shape == (2, 3)
    np.testing.assert_allclose(got, expected)
    if verbose:
        print("repeated-axis trace and ellipsis diagonal ok")


def case_errors(verbose: bool = False) -> None:
    np, einsum = _import_runtime()
    x = np.ones((5, 3), dtype="float32")
    y = np.ones((3, 2), dtype="float32")

    _expect_error(lambda: einsum(x, "row column"), ["Einsum pattern must contain", "->"], "missing arrow")
    _expect_error(
        lambda: einsum("row column -> row", x),
        ["last argument", "must be a string"],
        "pattern first",
    )
    _expect_error(
        lambda: einsum(x, "row column -> (row column)"),
        ["Shape rearrangement is not yet supported in einsum"],
        "grouped output axis",
    )
    _expect_error(
        lambda: einsum(np.ones((5, 1), dtype="float32"), "row () -> row"),
        ["Singleton () axes are not yet supported"],
        "singleton axis",
    )
    _expect_error(
        lambda: einsum(np.ones((5, 2), dtype="float32"), "row 2 -> row"),
        ["Anonymous axes are not yet supported"],
        "anonymous numeric axis",
    )
    _expect_error(
        lambda: einsum(x, y, "row column, column out -> row row"),
        ["duplicate dimension"],
        "duplicate output axis",
    )
    if verbose:
        print("expected einsum errors ok")


def run(case: str, verbose: bool = False) -> None:
    cases = {
        "basic": case_basic,
        "attention": case_attention,
        "ellipsis": case_ellipsis,
        "repeated": case_repeated_axes,
        "errors": case_errors,
    }
    selected = cases.keys() if case == "all" else [case]
    for name in selected:
        cases[name](verbose=verbose)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run deterministic smoke checks for einops.einsum.")
    parser.add_argument(
        "--case",
        choices=["all", "basic", "attention", "ellipsis", "repeated", "errors"],
        default="all",
        help="Subset of smoke checks to run (default: all).",
    )
    parser.add_argument("--verbose", action="store_true", help="Print each successful case.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run(args.case, verbose=args.verbose)
    print(f"einsum smoke passed: {args.case}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
