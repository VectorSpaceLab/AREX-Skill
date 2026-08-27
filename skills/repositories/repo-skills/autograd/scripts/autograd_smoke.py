#!/usr/bin/env python3
"""Minimal install-and-import smoke for Autograd.

The script checks the base differentiation surface and optionally the SciPy
wrapper surface. It uses tiny in-memory arrays only.
"""

from __future__ import annotations

import argparse
from importlib.metadata import version

import numpy as onp


def close(name, actual, expected, atol=1e-8, rtol=1e-8):
    actual_arr = onp.asarray(actual)
    expected_arr = onp.asarray(expected)
    if not onp.allclose(actual_arr, expected_arr, atol=atol, rtol=rtol):
        raise AssertionError(f"{name}: expected {expected_arr!r}, got {actual_arr!r}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Smoke-test the Autograd install and core differentiation surface.")
    parser.add_argument(
        "--require-scipy",
        action="store_true",
        help="Fail if the optional SciPy wrapper surface is unavailable.",
    )
    args = parser.parse_args(argv)

    try:
        import autograd
        import autograd.numpy as np
        from autograd import grad, jacobian, value_and_grad
    except ModuleNotFoundError as exc:
        if exc.name == "autograd":
            raise SystemExit("Autograd is not installed; run pip install autograd or pip install -e '.[scipy]' from a checkout.") from exc
        raise

    print(f"autograd {version('autograd')}")
    print(f"package file: {autograd.__file__}")

    x = np.array([0.1, 0.2])
    f = lambda v: np.sum(np.sin(v) ** 2)
    g = grad(f)(x)
    value, value_grad = value_and_grad(f)(x)
    J = jacobian(lambda v: np.array([v[0] + v[1], v[0] * v[1]]))(np.array([1.0, 2.0]))

    close("grad", g, 2.0 * onp.sin(onp.asarray(x)) * onp.cos(onp.asarray(x)))
    close("value", value, f(x))
    close("value_and_grad", value_grad, g)
    close("jacobian", J, onp.array([[1.0, 1.0], [2.0, 1.0]]))

    try:
        from autograd.scipy import special
    except ModuleNotFoundError as exc:
        if exc.name != "scipy":
            raise
        if args.require_scipy:
            raise SystemExit('SciPy is required for this smoke; install "autograd[scipy]" or "scipy".') from exc
        print('SciPy not installed; skipping the optional autograd.scipy smoke.')
    else:
        lse = special.logsumexp(np.array([1.0, 2.0, 3.0]))
        close("scipy.special.logsumexp", lse, onp.log(onp.exp(onp.array([1.0, 2.0, 3.0])).sum()))
        print(f"scipy.special.logsumexp={float(lse)}")

    print("autograd smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
