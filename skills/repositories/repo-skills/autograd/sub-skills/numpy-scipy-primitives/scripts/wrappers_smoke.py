#!/usr/bin/env python3
"""Tiny smoke helper for autograd.numpy and autograd.scipy wrappers.

The default run uses only tiny in-memory arrays and does not download data.
Use --simulate-missing to review the optional-dependency skip messages.
"""

from __future__ import annotations

import argparse
import json
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as onp


class MissingOptionalDependency(RuntimeError):
    def __init__(self, package: str, hint: str):
        super().__init__(hint)
        self.package = package
        self.hint = hint


def find_repo_root(start: Path | None = None) -> Path:
    here = (start or Path(__file__)).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "pyproject.toml").is_file() and (parent / "autograd" / "__init__.py").is_file():
            return parent
    return here.parent


def add_check(report, name, status, detail, hint=None):
    item = {"name": name, "status": status, "detail": detail}
    if hint:
        item["hint"] = hint
    report["checks"].append(item)
    return item


def close(name, actual, expected, atol=1e-8, rtol=1e-8):
    actual_arr = onp.asarray(actual)
    expected_arr = onp.asarray(expected)
    if not onp.allclose(actual_arr, expected_arr, atol=atol, rtol=rtol):
        raise AssertionError(f"{name}: expected {expected_arr!r}, got {actual_arr!r}")
    return actual_arr


def run_check(report, name, func, required=True):
    try:
        detail = func()
    except MissingOptionalDependency as exc:
        status = "failed" if required else "skipped"
        add_check(report, name, status, f"{exc.package} unavailable", exc.hint)
    except AssertionError as exc:
        add_check(report, name, "failed", str(exc))
    except Exception as exc:
        add_check(report, name, "failed", f"{type(exc).__name__}: {exc}")
    else:
        add_check(report, name, "passed", detail)


def import_autograd_modules():
    root = find_repo_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    import autograd.numpy as np
    from autograd import grad

    return np, grad


def import_optional_scipy(simulated_missing):
    if "scipy" in simulated_missing:
        raise MissingOptionalDependency("scipy", 'Install "autograd[scipy]" or "scipy" to enable autograd.scipy.')
    try:
        import autograd.scipy as asp
    except ModuleNotFoundError as exc:
        if exc.name == "scipy":
            raise MissingOptionalDependency("scipy", 'Install "autograd[scipy]" or "scipy" to enable autograd.scipy.') from exc
        raise
    return asp


def import_optional_xarray(simulated_missing):
    if "xarray" in simulated_missing:
        raise MissingOptionalDependency("xarray", "Install xarray to run DataArray interoperability examples.")
    try:
        import xarray as xr
    except ModuleNotFoundError as exc:
        if exc.name == "xarray":
            raise MissingOptionalDependency("xarray", "Install xarray to run DataArray interoperability examples.") from exc
        raise
    return xr


def check_numpy_grad(np, grad):
    x = np.array([-0.5, 0.25, 1.5])

    def loss(v):
        return np.sum(np.sin(v) ** 2 + np.maximum(v, 0.0))

    g = grad(loss)(x)
    expected = 2.0 * onp.sin(onp.asarray(x)) * onp.cos(onp.asarray(x)) + onp.array([0.0, 1.0, 1.0])
    close("numpy.grad.sin.maximum", g, expected)
    return f"gradient={onp.asarray(g).tolist()}"


def check_numpy_mean(np):
    value = np.mean([1.0, 2.0, 3.0])
    close("numpy.mean_list", value, 2.0)
    return f"value={float(value)}"


def check_numpy_concatenate(np):
    value = np.concatenate([np.array([1.0]), np.array([2.0])])
    close("numpy.concatenate", value, onp.array([1.0, 2.0]))
    return f"value={onp.asarray(value).tolist()}"


def check_numpy_dot(np):
    value = np.dot(np.array([1.0, 2.0]), np.array([3.0, 4.0]))
    close("numpy.dot", value, 11.0)
    return f"value={float(value)}"


def check_numpy_norm(np):
    value = np.linalg.norm([3.0, 4.0])
    close("numpy.linalg.norm_list", value, 5.0)
    return f"value={float(value)}"


def check_numpy_complex_norm(np):
    value = np.linalg.norm(np.array([1.0 + 2.0j, 3.0 - 4.0j]))
    close("numpy.linalg.norm_complex", value, onp.sqrt(30.0))
    return f"value={value!r}"


def check_numpy_fft_roundtrip(np):
    fft_x = np.array([1.0, 0.0, -1.0, 2.0])
    value = np.fft.ifft(np.fft.fft(fft_x))
    close("numpy.fft_roundtrip", value, fft_x)
    return f"value={onp.asarray(value).tolist()}"


def run_numpy_checks(np, grad, report):
    run_check(report, "numpy.grad.sin.maximum", lambda: check_numpy_grad(np, grad))
    run_check(report, "numpy.mean_list", lambda: check_numpy_mean(np))
    run_check(report, "numpy.concatenate", lambda: check_numpy_concatenate(np))
    run_check(report, "numpy.dot", lambda: check_numpy_dot(np))
    run_check(report, "numpy.linalg.norm_list", lambda: check_numpy_norm(np))
    run_check(report, "numpy.linalg.norm_complex", lambda: check_numpy_complex_norm(np))
    run_check(report, "numpy.fft_roundtrip", lambda: check_numpy_fft_roundtrip(np))


def check_scipy_logsumexp(np, asp):
    value = asp.special.logsumexp(np.array([1.0, 2.0, 3.0]))
    close("scipy.special.logsumexp", value, onp.log(onp.exp(onp.array([1.0, 2.0, 3.0])).sum()))
    return f"value={float(value)}"


def check_scipy_convolve(np, asp):
    value = asp.signal.convolve(np.array([1.0, 2.0, 3.0]), np.array([0.5, -1.0]), mode="full")
    expected = onp.convolve(onp.array([1.0, 2.0, 3.0]), onp.array([0.5, -1.0]), mode="full")
    close("scipy.signal.convolve", value, expected)
    return f"value={onp.asarray(value).tolist()}"


def check_scipy_solve_triangular(np, asp):
    import autograd.scipy.linalg as spla

    tri = np.array([[2.0, 0.0], [1.0, 3.0]])
    rhs = np.array([2.0, 5.0])
    value = spla.solve_triangular(tri, rhs, lower=True)
    close("scipy.linalg.solve_triangular", value, onp.array([1.0, 4.0 / 3.0]))
    return f"value={onp.asarray(value).tolist()}"


def check_scipy_norm_logpdf(asp):
    value = asp.stats.norm.logpdf(0.5, loc=0.5, scale=2.0)
    close("scipy.stats.norm.logpdf", value, -0.5 * onp.log(2.0 * onp.pi * 4.0))
    return f"value={float(value)}"


def check_scipy_odeint(np, asp):
    def rhs_fun(y, t, a):
        return -a * y

    t = np.linspace(0.0, 1.0, 4)
    value = asp.integrate.odeint(rhs_fun, np.array([1.0]), t, args=(0.5,))
    close("scipy.integrate.odeint", value[:, 0], onp.exp(-0.5 * onp.asarray(t)), atol=1e-5, rtol=1e-5)
    return f"trajectory={onp.asarray(value[:, 0]).tolist()}"


def run_scipy_checks(np, asp, report):
    run_check(report, "scipy.special.logsumexp", lambda: check_scipy_logsumexp(np, asp))
    run_check(report, "scipy.signal.convolve", lambda: check_scipy_convolve(np, asp))
    run_check(report, "scipy.linalg.solve_triangular", lambda: check_scipy_solve_triangular(np, asp))
    run_check(report, "scipy.stats.norm.logpdf", lambda: check_scipy_norm_logpdf(asp))
    run_check(report, "scipy.integrate.odeint", lambda: check_scipy_odeint(np, asp))


def check_xarray_grad(np, grad, xr):
    base = xr.DataArray(np.array([0.25, 1.0, -1.5]), dims=["feature"])

    def loss(weights):
        out = np.sin(base * weights) + np.maximum(base * weights, 0.0)
        return np.sum(out.data)

    weights = np.array([1.2, -0.7, 0.4])
    actual = grad(loss)(weights)
    z = onp.asarray(base.data) * onp.asarray(weights)
    expected = onp.asarray(base.data) * onp.cos(z) + onp.asarray(base.data) * (z > 0)
    close("xarray.grad.sin.maximum", actual, expected)
    return f"gradient={onp.asarray(actual).tolist()}"


def run_xarray_checks(np, grad, xr, report):
    run_check(report, "xarray.grad.sin.maximum", lambda: check_xarray_grad(np, grad, xr))


def summarize(report):
    counts = {"passed": 0, "skipped": 0, "failed": 0}
    for item in report["checks"]:
        counts[item["status"]] += 1
    report["summary"] = counts
    return counts


def print_human(report):
    for item in report["checks"]:
        prefix = {"passed": "[pass]", "skipped": "[skip]", "failed": "[fail]"}[item["status"]]
        print(f"{prefix} {item['name']}: {item['detail']}")
        if item.get("hint"):
            print(f"       hint: {item['hint']}")
    counts = report["summary"]
    print(f"Summary: {counts['passed']} passed, {counts['skipped']} skipped, {counts['failed']} failed")
    if report.get("versions"):
        print("Versions:", ", ".join(f"{k}={v}" for k, v in report["versions"].items()))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Smoke-test autograd.numpy and autograd.scipy wrapper behavior.")
    parser.add_argument("--json", action="store_true", help="Print a JSON report instead of human-readable text.")
    parser.add_argument("--strict", action="store_true", help="Fail if any optional section is skipped.")
    parser.add_argument(
        "--require-scipy",
        action="store_true",
        help="Treat the SciPy wrapper section as required instead of optional.",
    )
    parser.add_argument(
        "--require-xarray",
        action="store_true",
        help="Treat the xarray container section as required instead of optional.",
    )
    parser.add_argument(
        "--simulate-missing",
        action="append",
        choices=["scipy", "xarray"],
        default=[],
        help="Pretend selected optional dependencies are missing so the skip message can be reviewed.",
    )
    args = parser.parse_args(argv)

    np, grad = import_autograd_modules()
    report = {"checks": [], "versions": {"numpy": np.__version__}}

    try:
        report["versions"]["autograd"] = version("autograd")
    except PackageNotFoundError:
        report["versions"]["autograd"] = "unknown"

    run_numpy_checks(np, grad, report)

    scipy_required = args.require_scipy or args.strict
    scipy_state = {}

    def import_scipy():
        asp = import_optional_scipy(args.simulate_missing)
        scipy_state["asp"] = asp
        try:
            import scipy as sp
        except Exception:
            pass
        else:
            report["versions"]["scipy"] = sp.__version__
        return "autograd.scipy imported successfully"

    run_check(report, "scipy.import", import_scipy, required=scipy_required)
    if "asp" in scipy_state:
        run_scipy_checks(np, scipy_state["asp"], report)

    xarray_required = args.require_xarray or args.strict
    xarray_state = {}

    def import_xarray():
        xr = import_optional_xarray(args.simulate_missing)
        xarray_state["xr"] = xr
        report["versions"]["xarray"] = xr.__version__
        return "xarray imported successfully"

    run_check(report, "xarray.import", import_xarray, required=xarray_required)
    if "xr" in xarray_state:
        run_xarray_checks(np, grad, xarray_state["xr"], report)

    summarize(report)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)

    exit_code = 0
    if report["summary"]["failed"]:
        exit_code = 1
    elif args.strict and report["summary"]["skipped"]:
        exit_code = 1
    elif scipy_required and any(item["name"] == "scipy.import" and item["status"] != "passed" for item in report["checks"]):
        exit_code = 1
    elif xarray_required and any(item["name"] == "xarray.import" and item["status"] != "passed" for item in report["checks"]):
        exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
