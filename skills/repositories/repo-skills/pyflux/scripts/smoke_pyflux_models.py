#!/usr/bin/env python3
"""Synthetic PyFlux model smoke checks grouped by generated sub-skill.

The checks use tiny local fixtures only: no network, credentials, large data, or
original repository tests are required. They are meant to validate that a PyFlux
environment can execute representative workflows, not to benchmark a model.

Examples:
  python smoke_pyflux_models.py --section univariate
  python smoke_pyflux_models.py --section all
  python smoke_pyflux_models.py --repo-root /path/to/pyflux --section gas
"""

from __future__ import print_function

import argparse
import os
import sys


def add_repo_root(repo_root):
    if repo_root:
        root = os.path.abspath(repo_root)
        if not os.path.isdir(root):
            raise SystemExit("--repo-root does not exist or is not a directory: %s" % root)
        sys.path.insert(0, root)


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def assert_finite_array(np, arr, message):
    values = np.asarray(arr, dtype=float)
    assert_true(np.isfinite(values).all(), message)


def assert_finite_latents(np, model, label):
    values = [z.value for z in model.latent_variables.z_list]
    assert_true(all(value is not None for value in values), "%s has unestimated latent variables" % label)
    assert_finite_array(np, values, "%s latent variables contain non-finite values" % label)


def assert_frame(np, frame, rows, label, columns=None):
    assert_true(hasattr(frame, "shape"), "%s did not return a pandas-like frame" % label)
    assert_true(frame.shape[0] == rows, "%s returned %s rows, expected %s" % (label, frame.shape[0], rows))
    if columns is not None:
        assert_true(frame.shape[1] == columns, "%s returned %s columns, expected %s" % (label, frame.shape[1], columns))
    assert_finite_array(np, frame.values, "%s contains non-finite values" % label)


def fit_default(model):
    return model.fit()


def fit_quiet(model, *args, **kwargs):
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        return model.fit(*args, **kwargs)


def section_univariate(np, pd, pf, full=False):
    rng = np.random.RandomState(101)
    n = 70
    y = np.zeros(n)
    noise = rng.normal(size=n)
    for t in range(1, n):
        y[t] = 0.65 * y[t - 1] + noise[t]

    arima = pf.ARIMA(data=y, ar=1, ma=1, family=pf.Normal())
    fit_default(arima)
    assert_finite_latents(np, arima, "ARIMA")
    assert_frame(np, arima.predict(h=3), 3, "ARIMA.predict")
    assert_frame(np, arima.predict_is(h=3), 3, "ARIMA.predict_is")

    x1 = rng.normal(size=n)
    yx = np.zeros(n)
    for t in range(1, n):
        yx[t] = 0.45 * yx[t - 1] + 0.6 * x1[t] + rng.normal(scale=0.4)
    df = pd.DataFrame({"y": yx, "x1": x1})
    arimax = pf.ARIMAX(data=df, formula="y~x1", ar=1, ma=1, family=pf.Normal())
    fit_default(arimax)
    assert_finite_latents(np, arimax, "ARIMAX")
    future = df.tail(4).copy()
    future["y"] = np.nan
    assert_frame(np, arimax.predict(h=3, oos_data=future), 3, "ARIMAX.predict")
    assert_frame(np, arimax.predict_is(h=3), 3, "ARIMAX.predict_is")

    nn = pf.NNAR(data=y, ar=2, units=2, layers=1, family=pf.Normal())
    nn.fit("BBVI", iterations=20, quiet_progress=True, record_elbo=True)
    assert_finite_latents(np, nn, "NNAR")
    assert_frame(np, nn.predict(h=3), 3, "NNAR.predict")
    return ["ARIMA", "ARIMAX", "NNAR"]


def section_volatility(np, pd, pf, full=False):
    rng = np.random.RandomState(202)
    n = 90
    scale = np.repeat([0.5, 1.2, 0.8], [30, 30, 30])
    returns = pd.DataFrame({"ret": scale * rng.normal(size=n)})

    garch = pf.GARCH(data=returns, p=1, q=1)
    fit_default(garch)
    assert_finite_latents(np, garch, "GARCH")
    assert_frame(np, garch.predict(h=3), 3, "GARCH.predict")
    assert_frame(np, garch.predict_is(h=3), 3, "GARCH.predict_is")

    egarch = pf.EGARCH(data=returns, p=1, q=1)
    egarch.add_leverage()
    fit_default(egarch)
    assert_finite_latents(np, egarch, "EGARCH leverage")

    checked = ["GARCH", "EGARCH+leverage"]

    if full:
        for cls in (pf.EGARCHM, pf.LMEGARCH, pf.SEGARCH, pf.SEGARCHM):
            model = cls(data=returns, p=1, q=1)
            fit_default(model)
            assert_finite_latents(np, model, cls.__name__)
            checked.append(cls.__name__)
        x = rng.normal(size=n)
        df = pd.DataFrame({"y": returns["ret"].values, "x": x})
        reg = pf.EGARCHMReg(data=df, p=1, q=1, formula="y~x")
        fit_default(reg)
        assert_finite_latents(np, reg, "EGARCHMReg")
        checked.append("EGARCHMReg fit")

    return checked


def section_gas(np, pd, pf, full=False):
    rng = np.random.RandomState(303)
    n = 80
    y = np.zeros(n)
    x1 = rng.normal(size=n)
    for t in range(1, n):
        y[t] = 0.55 * y[t - 1] + 0.35 * x1[t] + rng.normal(scale=0.4)
    df = pd.DataFrame({"y": y, "x1": x1})

    gas = pf.GAS(data=df, ar=1, sc=1, family=pf.Normal())
    fit_default(gas)
    assert_finite_latents(np, gas, "GAS")
    assert_frame(np, gas.predict(h=3), 3, "GAS.predict")

    gasx = pf.GASX(data=df, formula="y ~ x1", ar=1, sc=1, family=pf.Normal())
    fit_default(gasx)
    assert_finite_latents(np, gasx, "GASX")
    oos = df.tail(4).copy()
    assert_frame(np, gasx.predict(h=3, oos_data=oos), 3, "GASX.predict")

    gasreg = pf.GASReg(formula="y ~ x1", data=df, family=pf.Normal())
    fit_default(gasreg)
    assert_finite_latents(np, gasreg, "GASReg")
    assert_frame(np, gasreg.predict(h=3, oos_data=oos), 3, "GASReg.predict")

    counts = pd.DataFrame({"events": rng.poisson(3, size=n)})
    level = pf.GASLLEV(data=counts, family=pf.Poisson())
    fit_default(level)
    assert_finite_latents(np, level, "GASLLEV")
    assert_frame(np, level.predict(h=3), 3, "GASLLEV.predict")

    trend = pf.GASLLT(data=pd.DataFrame({"signal": np.cumsum(rng.normal(size=n))}), family=pf.Normal())
    fit_default(trend)
    assert_finite_latents(np, trend, "GASLLT")
    assert_frame(np, trend.predict(h=3), 3, "GASLLT.predict")

    games = pd.DataFrame({
        "HomeTeam": ["A", "B", "C", "A", "B", "C", "A", "C", "B", "A", "D", "D"],
        "AwayTeam": ["B", "C", "A", "C", "A", "B", "D", "B", "D", "C", "A", "B"],
        "PointsDiff": [7, -3, 4, 5, 1, 2, 6, -1, 0, 3, -2, 1],
    })
    rank = pf.GASRank(data=games, team_1="HomeTeam", team_2="AwayTeam", score_diff="PointsDiff", family=pf.Normal())
    fit_default(rank)
    assert_finite_latents(np, rank, "GASRank")
    prediction = rank.predict("A", "B", neutral=True)
    assert_finite_array(np, prediction, "GASRank.predict contains non-finite values")

    return ["GAS", "GASX", "GASReg", "GASLLEV", "GASLLT", "GASRank"]


def section_state_space(np, pd, pf, full=False):
    rng = np.random.RandomState(404)
    n = 65
    series = np.cumsum(rng.normal(size=n))
    df = pd.DataFrame({"y": series, "x1": rng.normal(size=n)})

    llev = pf.LLEV(data=df, target="y")
    fit_default(llev)
    assert_finite_latents(np, llev, "LLEV")
    assert_frame(np, llev.predict(h=3), 3, "LLEV.predict")

    llt = pf.LLT(data=df, target="y")
    fit_default(llt)
    assert_finite_latents(np, llt, "LLT")
    assert_frame(np, llt.predict(h=3), 3, "LLT.predict")

    dar = pf.DAR(data=df, ar=1, target="y")
    fit_default(dar)
    assert_finite_latents(np, dar, "DAR")
    assert_frame(np, dar.predict(h=3), 3, "DAR.predict")

    dyn = pf.DynamicGLM(formula="y ~ x1", data=df, family=pf.Normal())
    assert_true(type(dyn).__name__ == "DynReg", "DynamicGLM Normal did not dispatch to DynReg")
    fit_default(dyn)
    assert_finite_latents(np, dyn, "DynReg")

    counts = pd.DataFrame({"y": rng.poisson(3, size=n), "x1": rng.normal(size=n)})
    nl = pf.LocalLevel(data=counts, family=pf.Poisson(), target="y")
    assert_true(type(nl).__name__ == "NLLEV", "LocalLevel Poisson did not dispatch to NLLEV")
    fit_quiet(nl, iterations=20, print_progress=False)
    assert_finite_latents(np, nl, "NLLEV")
    assert_frame(np, nl.predict(h=3), 3, "NLLEV.predict")

    nd = pf.DynamicGLM(formula="y ~ x1", data=counts, family=pf.Poisson())
    assert_true(type(nd).__name__ == "NDynReg", "DynamicGLM Poisson did not dispatch to NDynReg")
    fit_quiet(nd, iterations=20, print_progress=False)
    assert_finite_latents(np, nd, "NDynReg")

    return ["LLEV", "LLT", "DAR", "DynReg", "NLLEV", "NDynReg"]


def section_multivariate(np, pd, pf, full=False):
    rng = np.random.RandomState(505)
    n = 60
    x = np.zeros(n)
    y = np.zeros(n)
    for t in range(1, n):
        x[t] = 0.55 * x[t - 1] + rng.normal(scale=0.3)
        y[t] = 0.25 * x[t - 1] + 0.45 * y[t - 1] + rng.normal(scale=0.3)
    df = pd.DataFrame({"x": x, "y": y})

    var = pf.VAR(data=df, lags=1)
    fit_default(var)
    assert_finite_latents(np, var, "VAR")
    assert_frame(np, var.predict(h=3), 3, "VAR.predict", columns=2)
    assert_frame(np, var.predict_is(h=3), 3, "VAR.predict_is", columns=2)

    gp_series = pd.DataFrame({"y": 0.7 * x + 0.2 * np.sin(x) + rng.normal(scale=0.1, size=n)})
    gp = pf.GPNARX(data=gp_series, ar=2, kernel=pf.SquaredExponential(), target="y")
    fit_default(gp)
    assert_finite_latents(np, gp, "GPNARX")
    assert_frame(np, gp.predict(h=3), 3, "GPNARX.predict", columns=1)

    if full:
        for kernel in (pf.OrnsteinUhlenbeck(), pf.RationalQuadratic(), pf.Periodic()):
            model = pf.GPNARX(data=gp_series, ar=2, kernel=kernel, target="y")
            fit_default(model)
            assert_finite_latents(np, model, "GPNARX %s" % kernel.__class__.__name__)
        # ARD is exported but not smoke-run here: PyFlux 0.4.17 attempts to use
        # pyflux.families.FLat inside ARD.build_latent_variables(), which raises
        # AttributeError because the public family class is Flat.

    return ["VAR", "GPNARX"]


SECTION_FUNCS = {
    "univariate": section_univariate,
    "volatility": section_volatility,
    "gas": section_gas,
    "state-space": section_state_space,
    "multivariate": section_multivariate,
}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run safe synthetic PyFlux model smoke checks.")
    parser.add_argument("--repo-root", help="Optional local PyFlux checkout to put on sys.path before import.")
    parser.add_argument("--section", choices=["all"] + sorted(SECTION_FUNCS), default="all")
    parser.add_argument("--full", action="store_true", help="Run slower optional model variants in selected sections.")
    args = parser.parse_args(argv)

    add_repo_root(args.repo_root)

    try:
        import numpy as np
        import pandas as pd
        import pyflux as pf
    except Exception as exc:
        raise SystemExit("Required import failed: %s: %s" % (exc.__class__.__name__, exc))

    sections = sorted(SECTION_FUNCS) if args.section == "all" else [args.section]
    for section in sections:
        print("[pyflux smoke] section=%s" % section)
        checked = SECTION_FUNCS[section](np, pd, pf, full=args.full)
        print("  ok: %s" % ", ".join(checked))

    print("[pyflux smoke] completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
